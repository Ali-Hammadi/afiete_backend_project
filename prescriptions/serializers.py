from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from appointments.models import Appointment
from .models import Prescription, PrescriptionMedication


def raise_serializer_validation(error):
    if hasattr(error, 'message_dict'):
        raise serializers.ValidationError(error.message_dict)
    raise serializers.ValidationError(error.messages)


class PrescriptionMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionMedication
        fields = ['id', 'medication_name', 'dosage', 'frequency', 'duration', 'notes']
        read_only_fields = ['id']
        extra_kwargs = {
            'notes': {'required': False, 'allow_blank': True},
        }


class PrescriptionReadSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    doctor_username = serializers.CharField(source='doctor.user.username', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    patient_username = serializers.CharField(source='patient.user.username', read_only=True)
    appointment_id = serializers.IntegerField(source='appointment.id', read_only=True)
    medications = PrescriptionMedicationSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'prescription_number',
            'doctor_id',
            'doctor_username',
            'patient_id',
            'patient_username',
            'appointment_id',
            'diagnosis',
            'notes',
            'medications',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class DoctorPrescriptionCreateSerializer(serializers.ModelSerializer):
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.select_related('doctor', 'patient').all(),
        source='appointment',
        write_only=True
    )
    medications = PrescriptionMedicationSerializer(many=True, write_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'appointment_id',
            'diagnosis',
            'notes',
            'medications',
            'prescription_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'prescription_number', 'created_at', 'updated_at']
        extra_kwargs = {
            'notes': {'required': False, 'allow_blank': True},
        }

    def validate_diagnosis(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Diagnosis is required.')
        return value

    def validate_medications(self, value):
        if not value:
            raise serializers.ValidationError('Prescription must contain at least one medication.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        doctor = getattr(getattr(request, 'user', None), 'doctor', None)
        appointment = attrs.get('appointment')

        if doctor is None:
            raise serializers.ValidationError({'detail': 'Only doctors can create prescriptions.'})

        errors = {}

        if appointment.doctor_id != doctor.id:
            errors['appointment_id'] = 'Appointment must belong to the authenticated doctor.'

        if appointment.status != Appointment.Status.COMPLETED:
            errors['appointment_id'] = 'Appointment status must be completed.'

        if Prescription.objects.filter(appointment=appointment).exists():
            errors['appointment_id'] = 'Only one prescription is allowed per appointment.'

        if errors:
            raise serializers.ValidationError(errors)

        attrs['doctor'] = doctor
        attrs['patient'] = appointment.patient
        return attrs

    def create(self, validated_data):
        medications_data = validated_data.pop('medications')

        try:
            with transaction.atomic():
                prescription = Prescription.objects.create(**validated_data)
                for medication_data in medications_data:
                    PrescriptionMedication.objects.create(
                        prescription=prescription,
                        **medication_data
                    )
                return prescription
        except DjangoValidationError as error:
            raise_serializer_validation(error)
        except IntegrityError:
            raise serializers.ValidationError({
                'appointment_id': 'Only one prescription is allowed per appointment.'
            })

    def to_representation(self, instance):
        return PrescriptionReadSerializer(instance, context=self.context).data


class DoctorPrescriptionUpdateSerializer(serializers.ModelSerializer):
    medications = PrescriptionMedicationSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'diagnosis',
            'notes',
            'medications',
            'prescription_number',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'prescription_number', 'created_at', 'updated_at']
        extra_kwargs = {
            'diagnosis': {'required': False},
            'notes': {'required': False, 'allow_blank': True},
        }

    def validate_diagnosis(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError('Diagnosis is required.')
        return value

    def validate_medications(self, value):
        if not value:
            raise serializers.ValidationError('Prescription must contain at least one medication.')
        return value

    def update(self, instance, validated_data):
        medications_data = validated_data.pop('medications', None)

        try:
            with transaction.atomic():
                instance = super().update(instance, validated_data)

                if medications_data is not None:
                    instance.medications.all().delete()
                    for medication_data in medications_data:
                        PrescriptionMedication.objects.create(
                            prescription=instance,
                            **medication_data
                        )

                return instance
        except DjangoValidationError as error:
            raise_serializer_validation(error)

    def to_representation(self, instance):
        return PrescriptionReadSerializer(instance, context=self.context).data
