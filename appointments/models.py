from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

class Appointment(models.Model):
    class Status(models.TextChoices):
        Pending = 'pending', 'Pending'          # محجوز بانتظار الدفع
        Confirmed = 'confirmed', 'Confirmed'    # مدفوع ومؤكد
        Cancelled = 'cancelled', 'Cancelled'    # ملغي
        Completed = 'completed', 'Completed'    # منتهي
        Expired = 'expired', 'Expired'          # انتهت صلاحية نافذة الحجز دون دفع
        Missed = 'missed', 'Missed'            # ➕ جلسة فائتة (لم يحضرها المريض)

    class Type(models.TextChoices):
        Video = 'video', 'Video'
        Audio = 'audio', 'Audio'
        TextMessage = 'text_message', 'Text Message'

    type = models.CharField(max_length=100, choices=Type.choices, default=Type.TextMessage)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateTimeField()
    duration = models.IntegerField()  # بالدقائق
    status = models.CharField(max_length=100, choices=Status.choices, default=Status.Pending)
    
    # ➕ متغير الكورس العلاجي: المريض هو من يحدد استمرارية الجلسات القادمة أو إغلاق الخطة العلاجية
    has_next_session = models.BooleanField(default=True, null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Mtg {self.pk} - {self.patient.user.username} with {self.doctor.user.username} ({self.status})"


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
        Pending = 'pending', 'Pending'
        Completed = 'completed', 'Completed'
        Refunded = 'refunded', 'Refunded'  # حالة الاسترداد المالي

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    doctor_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_transferred_to_doctor = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.Pending)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.amount} for Appt {self.appointment.pk} ({self.status})"


class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.rating} for {self.doctor.user.username}"