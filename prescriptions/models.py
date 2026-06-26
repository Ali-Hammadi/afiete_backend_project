from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient


class Prescription(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='prescriptions'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name='prescription'
    )
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    prescription_number = models.CharField(max_length=40, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', '-created_at'], name='rx_doctor_created_idx'),
            models.Index(fields=['patient', '-created_at'], name='rx_patient_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(diagnosis=''),
                name='rx_diagnosis_not_blank'
            )
        ]

    def __str__(self):
        return self.prescription_number or f'Prescription {self.pk}'

    @staticmethod
    def generate_prescription_number():
        date_prefix = timezone.now().strftime('%Y%m%d')
        allowed_chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

        for _ in range(10):
            random_part = get_random_string(8, allowed_chars=allowed_chars)
            number = f'RX-{date_prefix}-{random_part}'
            if not Prescription.objects.filter(prescription_number=number).exists():
                return number

        raise RuntimeError('Could not generate a unique prescription number.')

    def clean(self):
        errors = {}

        if not self.diagnosis or not self.diagnosis.strip():
            errors['diagnosis'] = 'Diagnosis is required.'

        if self.appointment_id:
            try:
                appointment = self.appointment
            except Appointment.DoesNotExist:
                errors['appointment'] = 'Appointment does not exist.'
            else:
                if self.doctor_id and appointment.doctor_id != self.doctor_id:
                    errors['doctor'] = 'Prescription doctor must match the appointment doctor.'

                if self.patient_id and appointment.patient_id != self.patient_id:
                    errors['patient'] = 'Prescription patient must match the appointment patient.'

                if appointment.status != Appointment.Status.COMPLETED:
                    errors['appointment'] = 'Prescription appointment must be completed.'

                duplicate = Prescription.objects.filter(appointment_id=self.appointment_id)
                if self.pk:
                    duplicate = duplicate.exclude(pk=self.pk)
                if duplicate.exists():
                    errors['appointment'] = 'This appointment already has a prescription.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()

        self.full_clean()
        super().save(*args, **kwargs)


class PrescriptionMedication(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='medications'
    )
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    frequency = models.CharField(max_length=255)
    duration = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(medication_name=''),
                name='rx_med_name_not_blank'
            ),
            models.CheckConstraint(
                condition=~models.Q(dosage=''),
                name='rx_med_dosage_not_blank'
            ),
            models.CheckConstraint(
                condition=~models.Q(frequency=''),
                name='rx_med_freq_not_blank'
            ),
            models.CheckConstraint(
                condition=~models.Q(duration=''),
                name='rx_med_duration_not_blank'
            ),
        ]

    def __str__(self):
        return self.medication_name

    def clean(self):
        errors = {}

        for field_name in ['medication_name', 'dosage', 'frequency', 'duration']:
            value = getattr(self, field_name)
            if not value or not value.strip():
                errors[field_name] = 'This field is required.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
