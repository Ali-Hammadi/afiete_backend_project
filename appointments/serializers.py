from decimal import Decimal
from rest_framework import serializers
from rest_framework.validators import ValidationError
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from django.db import transaction

from ratings.serializers import RatingReadSerializer
from .models import Appointment, SessionPrice, Payment
from doctors.models import Doctor, Schedule
from assessments.serializers import ScoresSerializer


class DoctorWalletSerializer(serializers.Serializer):
    total_earnings = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Total earnings of the doctor from completed sessions."
    )
    transferred_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Amounts already transferred to the doctor's bank account."
    )
    pending_clearance = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Pending amounts available for withdrawal."
    )


class PricesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPrice
        fields = ['id', 'duration', 'type', 'price']
        read_only_fields = ['duration']

    def validate_price(self, value):
        if value < 0:
            raise ValidationError('Price cannot be negative.')
        return value

    def create(self, validated_data):
        session_type = validated_data.get('type')
        doctor = self.context['request'].user.doctor

        if SessionPrice.objects.filter(doctor=doctor, type=session_type).exists():
            raise ValidationError(f'Session type "{session_type}" configuration already exists for this doctor.')
        
        return SessionPrice.objects.create(doctor=doctor, duration=30, **validated_data)

    def update(self, instance, validated_data):
        session_type = validated_data.get('type', instance.type)

        if SessionPrice.objects.filter(doctor=instance.doctor, type=session_type).exclude(pk=instance.pk).exists():
            raise ValidationError(f'Session type "{session_type}" already exists.')

        instance.type = session_type
        instance.price = validated_data.get('price', instance.price)
        instance.duration = 30
        instance.save()
        return instance


class SlotSerializer(serializers.Serializer):
    start = serializers.TimeField()
    end = serializers.TimeField()


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(write_only=True)
    slot = SlotSerializer(write_only=True)
    day_date = serializers.DateField(write_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor_username', 'type', 'day_date', 'slot', 'status', 'date', 'has_next_session']
        read_only_fields = ['status', 'date', 'has_next_session']

    def validate(self, attrs):
        doctor_username = attrs.get('doctor_username')
        start_time = attrs['slot']['start']
        end_time = attrs['slot']['end']
        day_date = attrs.get('day_date')
        
        try:
            doctor = Doctor.objects.get(user__username=doctor_username)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError({"doctor_username": "Doctor does not exist."})
        
        naive_start_datetime = datetime.combine(day_date, start_time)
        naive_end_datetime = datetime.combine(day_date, end_time)
        start_datetime = timezone.make_aware(naive_start_datetime)
        end_datetime = timezone.make_aware(naive_end_datetime)

        if start_datetime < timezone.now():
            raise serializers.ValidationError({"date": "It is not possible to book an appointment earlier than now."})

        if start_time >= end_time: 
            raise serializers.ValidationError({"slot": "End time must be greater than start time."})

        if (end_datetime - start_datetime) < timedelta(minutes=30): 
            raise serializers.ValidationError({"slot": "Duration must be at least 30 minutes."})

        day_name = day_date.strftime('%A')
        is_within_schedule = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_name,
            start_time__lte=start_time,
            end_time__gte=end_time
        ).exists()

        if not is_within_schedule:
            raise serializers.ValidationError(
                {"slot": f"This time is outside the doctor's official working hours for {day_name}."}
            )

        overlapping_appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed']
        )
        if self.instance:
            overlapping_appointments = overlapping_appointments.exclude(pk=self.instance.pk)

        for app in overlapping_appointments:
            duration = getattr(app, 'duration', 30)
            app_start = app.date
            app_end = app.date + timedelta(minutes=duration)
            if start_datetime < app_end and end_datetime > app_start:
                raise serializers.ValidationError(
                    {"slot": "This slot overlaps with an existing appointment for this doctor."}
                )

        attrs['doctor'] = doctor
        attrs['date'] = start_datetime
        
        attrs.pop('doctor_username')
        attrs.pop('day_date')
        attrs.pop('slot')
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'patient'):
            validated_data['patient'] = request.user.patient
        return super().create(validated_data)


# --- Updated to English Error Message ---
class RescheduleAppointmentSerializer(AppointmentSerializer):
    class Meta(AppointmentSerializer.Meta):
        fields = ['doctor_username', 'day_date', 'slot']

    def validate(self, attrs):
        if self.instance and self.instance.status not in [Appointment.Status.Confirmed, Appointment.Status.Missed]:
            raise ValidationError("You can only reschedule confirmed or missed appointments.")
        return super().validate(attrs)


class AppointmentListSerializer(serializers.ModelSerializer): 
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    doctor_username = serializers.CharField(source="doctor.user.username", read_only=True)

    class Meta: 
        model = Appointment
        fields = ['id', 'patient_username', 'doctor_username', 'date', 'type', 'status', 'has_next_session']


class PatientSerializer(serializers.Serializer): 
    scores = ScoresSerializer(read_only=True, source='*')
    nickname = serializers.CharField(read_only=True)
    psychological_history = serializers.CharField(read_only=True)


class RetrieveAppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    doctor_username = serializers.CharField(source='doctor.user.username', read_only=True)

    class Meta: 
        model = Appointment
        fields = ['id', 'patient', 'patient_username', 'doctor_username', 'date', 'type', 'status', 'has_next_session']


class PaymentSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'appointment_id', 'amount', 'method', 'transaction_id', 'status', 'date', 'admin_commission', 'doctor_amount', 'is_transferred_to_doctor']
        read_only_fields = ['status', 'amount', 'date', 'admin_commission', 'doctor_amount', 'is_transferred_to_doctor']

    def validate_transaction_id(self, value):
        method = self.initial_data.get('method')
        if Payment.objects.filter(transaction_id=value, method=method).exists():
            raise serializers.ValidationError("This transaction ID already exists for this payment method.")
        return value

    def validate_appointment_id(self, value):
        request = self.context.get('request')
        try:
            appointment = Appointment.objects.get(pk=value, patient=request.user.patient)
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Appointment not found or unauthorized.")

        if appointment.status != 'pending':
            raise serializers.ValidationError("This appointment is not pending payment.")

        if hasattr(appointment, 'payment'):
            raise serializers.ValidationError("Payment record already exists for this appointment.")

        return value

    def create(self, validated_data):
        appointment_id = validated_data.pop('appointment_id')
        appointment = Appointment.objects.get(pk=appointment_id)

        try:
            session_price_config = SessionPrice.objects.get(doctor=appointment.doctor, type=appointment.type)
            total_amount = session_price_config.price
        except SessionPrice.DoesNotExist:
            raise serializers.ValidationError({"detail": "Active pricing configuration missing for this session profile."})

        commission_rate = Decimal('0.10') 
        admin_commission_value = total_amount * commission_rate
        doctor_amount_value = total_amount - admin_commission_value

        with transaction.atomic():
            payment = Payment.objects.create(
                appointment=appointment,
                amount=total_amount,
                admin_commission=admin_commission_value,
                doctor_amount=doctor_amount_value,
                status='completed', 
                **validated_data
            )
            appointment.status = Appointment.Status.Confirmed
            appointment.save()
            
        return payment


class DoctorMinimalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Doctor
        fields = ['id', 'username']


class PastAppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorMinimalSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'date', 'type', 'status', 'has_next_session', 'created_at']


class DoctorProfileSerializer(serializers.ModelSerializer):
    reviews = RatingReadSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'reviews', 'average_rating']

    def get_average_rating(self, obj):
        average = obj.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return round(average, 1) if average else 0.0


# --- Optimized & Corrected for the 5-Minute Rule ---
class PatientUpdateNextSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['has_next_session']

    def validate(self, attrs):
        # The choice must happen while the session is Confirmed/Ongoing (5 minutes before the end)
        if self.instance.status != Appointment.Status.Confirmed:
            raise ValidationError("You can only decide on the next session during an active, confirmed appointment.")
        return attrs