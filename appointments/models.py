from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings

from django.contrib.auth import get_user_model
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
        MISSED = 'missed', 'Missed'  # Doctor No-Show
        PATIENT_MISSED = 'patient_missed', 'Patient Missed'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        TRANSFERRED = 'transferred', 'Transferred to Doctor'
        REFUNDED = 'refunded', 'Refunded'
        PARTIAL = 'partial', 'Partial Payment'
    
    class Type(models.TextChoices):
        CHAT = 'chat', 'Chat'       # دردشة
        VOICE = 'voice', 'Voice'     # صوت
        VIDEO = 'video', 'Video'     # فيديو

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CHAT)
    date = models.DateTimeField()

    def __str__(self):
        return f"Appointment {self.id} - {self.status}"


class SessionPrice(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='session_prices')
    duration = models.IntegerField(default=30)
    type = models.CharField(max_length=100, choices=Appointment.Type.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('doctor', 'type')

    def __str__(self):
        return f"{self.type} - {self.price} MRU"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        REFUNDED = 'refunded', 'Refunded'
        REJECTED = 'rejected', 'Rejected'

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    
    # تفاصيل المبالغ المالية
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_commission = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    doctor_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    
    # تفاصيل العملية والحالة
    method = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_transferred_to_doctor = models.BooleanField(default=False)
    
    # التواريخ
    date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        حساب تلقائي لعمولة التطبيق ومستحقات الطبيب بناءً على النسبة
        الموجودة في ملف settings.py قبل حفظ البيانات في قاعدة البيانات.
        """
        if self.amount:
            # تحويل القيم إلى Decimal لضمان دقة الحسابات المالية
            amount_decimal = Decimal(str(self.amount))
            commission_rate = Decimal(str(settings.COMMISSION_RATE))
            
            # العمليات الحسابية
            self.admin_commission = amount_decimal * commission_rate
            self.doctor_amount = amount_decimal - self.admin_commission
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.amount} for Appt {self.appointment.pk} ({self.status})"