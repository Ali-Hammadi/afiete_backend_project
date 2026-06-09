from rest_framework import serializers
from rest_framework.validators import ValidationError

from .models import *
from doctors.models import Doctor, Schedule

from django.utils import timezone
from datetime import datetime, timedelta

from patients.models import Patient
from assessments.serializers import ScoresSerializer
class PricesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPrice
        fields = ['duration','type','price']
        read_only_fields = ['duration']

    def validate_price(self, value):
        if value < 0:
            raise ValidationError('invalid price')
        return value

    def create(self, validated_data):
        session_type = validated_data.get('type')

        doctor = self.context['request'].user.doctor

        if SessionPrice.objects.filter(doctor=doctor, type=session_type).exists():
            raise ValidationError(f'Session type {session_type} already exists')
        
        return SessionPrice.objects.create(
            doctor=doctor,
            duration=30,
            **validated_data
        )

    def update(self, instance, validated_data):
        session_type = validated_data.get('type', instance.type)

        if SessionPrice.objects.filter(
            doctor=instance.doctor,
            type=session_type,
        ).exclude(pk=instance.pk).exists():
            raise ValidationError(f'Session type {session_type} already exists')

        instance.type = session_type
        instance.price = validated_data.get('price', instance.price)
        instance.duration = 30
        instance.save()
        return instance

class SlotSerializer(serializers.Serializer):
    start = serializers.TimeField()
    end = serializers.TimeField()

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(write_only=True) # لإدخال اسم المستخدم للطبيب بدلاً من ID
    slot = SlotSerializer(write_only=True) # لتمرير وقت البداية والنهاية ككائن واحد
    day_date = serializers.DateField(write_only=True) # لتمرير تاريخ اليوم الذي سيتم الحجز فيه
    class Meta:
        model = Appointment
        fields = ['id', 'doctor_username', 'type','day_date', 'slot', 'status']
        read_only_fields = ['status'] # لكي لا يقوم المستخدم بتعديل الحالة بنفسه

    def validate(self, attrs):
        doctor_username = attrs.get('doctor_username')
        
        start_time = attrs['slot']['start']
        end_time = attrs['slot']['end']
        day_date = attrs.pop('day_date')
        attrs.pop('slot') # إ
        # التحقق من وجود الطبيب
        try:
            doctor = Doctor.objects.get(user__username=doctor_username)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError({"doctor_username": "Doctor not exists"})
        
        
        naive_start_datetime = datetime.combine(day_date, start_time)
        naive_end_datetime = datetime.combine(day_date, end_time)
        
        start_datetime = timezone.make_aware(naive_start_datetime)
        end_datetime = timezone.make_aware(naive_end_datetime)

        if start_datetime < timezone.now():
            raise serializers.ValidationError({"date": "It is not possible to book an appointment earlier than now."})

        if start_time > end_time: 
            raise serializers.ValidationError({"detail":'end time should be greater than start time'})
        day_name = day_date.strftime('%A') # الحصول على اسم اليوم بالإنجليزية

        if (end_datetime - start_datetime) < timedelta(minutes=30): 
            raise serializers.ValidationError({"detail": "duration at lease 30 minutes"})

        # 3. التحقق من أوقات دوام الطبيب (Schedule)
        is_within_schedule = Schedule.objects.filter(
            doctor=doctor,
            day_of_week=day_name,
            start_time__lte=start_time,
            end_time__gte=end_time
        ).exists()

        if not is_within_schedule:
            raise serializers.ValidationError(
                {"date": f"This time is outside the doctor's official working hours for the day ({day_name})."}
            )

        overlapping_appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=['pending', 'confirmed'] # فحص الحجوزات النشطة فقط
        )
        if self.instance:
            overlapping_appointments = overlapping_appointments.exclude(pk=self.instance.pk)
        for app in overlapping_appointments:
            app_start = app.date
            app_end = app.date + timedelta(minutes=app.duration)

            if start_datetime < app_end and end_datetime > app_start:
                raise serializers.ValidationError(
                    {"date": "This appointment overlaps with another existing doctor's appointment."}
                )

        attrs['doctor'] = doctor

        # اضافة الحقول المحسوبة إلى البيانات المعالجة
        attrs.pop('doctor_username')
        date = start_datetime
        attrs['date'] = date
        duration = int((end_datetime - start_datetime).total_seconds() / 60) # حساب المدة بالدقائق
        attrs['duration'] = duration



        return attrs

    def create(self, validated_data):
        validated_data.pop('doctor_username', None)
        
        request = self.context.get('request')
        if request and hasattr(request.user, 'patient'):
            validated_data['patient'] = request.user.patient
           
        return super().create(validated_data)

class AppointmentListSerializer(serializers.ModelSerializer): 
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    doctor_username = serializers.CharField(source="doctor.user.username",read_only=True)
    class Meta: 
        model = Appointment
        fields = ['id','patient_username','doctor_username', 'date', 'duration', 'type', 'status']  

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
        fields = ['id','patient','patient_username','doctor_username', 'date', 'duration', 'type', 'status']  


class RescheduleAppointmentSerializer(AppointmentSerializer):
    
    class Meta(AppointmentSerializer.Meta):
        fields = ['doctor_username','day_date', 'slot']
    def validate(self, attrs):
        print("validate called", attrs)
        return super().validate(attrs)
    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.duration = validated_data.get('duration', instance.duration)
        instance.save()
        return instance
    

class PaymentSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'appointment_id', 'amount', 'method', 'transaction_id', 'status', 'date']
        read_only_fields = ['status', 'amount', 'date']


    def validate_transaction_id(self, value):
        method = self.initial_data.get('method')
        if Payment.objects.filter(transaction_id=value, method=method).exists():
            raise serializers.ValidationError("This transaction ID already exists for this payment method.")
        return value
    def validate_appointment_id(self, value):
        request = self.context.get('request')
        try:
            appointment = Appointment.objects.get(
                pk=value,
                patient=request.user.patient
            )
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Appointment not found.")

        if appointment.status != 'pending':
            raise serializers.ValidationError("This appointment is not pending payment.")

        # تحقق ما في دفع موجود مسبقاً
        if hasattr(appointment, 'payment'):
            raise serializers.ValidationError("Payment already exists for this appointment.")

        return value

    def create(self, validated_data):
        appointment_id = validated_data.pop('appointment_id')
        appointment = Appointment.objects.get(pk=appointment_id)

        # احسب المبلغ تلقائياً من مدة الحجز وسعر الطبيب
        
        session_price = SessionPrice.objects.filter(
            doctor = appointment.doctor,
            type =appointment.type, 
        ).first().price
        amount = (session_price)
        payment = Payment.objects.create(
            appointment=appointment,
            amount=amount,
            **validated_data
        )
        return payment
