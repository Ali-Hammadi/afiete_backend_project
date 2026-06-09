from django.db import models
from django.utils import timezone
from users.models import User
from patients.models import Patient
from doctors.models import Doctor
from datetime import datetime
class Appointment(models.Model):
    class Status (models.TextChoices):
        Pending = 'pending'      # تم الحجز، بانتظار الدفع
        Confirmed = 'confirmed'  # تم الدفع
        Cancelled = 'cancelled'  # ملغي
        Completed = 'completed'  # انتهى الموعد
        Expired = 'expired'      # انتهى وقته بدون دفع
        
    class Type(models.TextChoices):
        Video = 'video' , 'Video'
        Audio = 'audio' , 'Audio'
        TextMessage = 'text_message' , 'Text Message'

    type = models.CharField(max_length=100 , choices=Type.choices , default=Type.TextMessage)
    patient = models.ForeignKey(Patient , on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.IntegerField() # in minutes
    status = models.CharField(max_length=100 , choices= Status.choices , default=Status.Pending)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_by = models.CharField(null=True, blank=True, max_length=20)
    def __str__(self):
        return f"Appointment between {self.patient} and {self.doctor} on {self.date} and id = {self.pk}"
    
    @property
    def end_time(self):
        return self.date + timezone.timedelta(minutes=self.duration)


class SessionPrice(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='session_prices',
    )
    class Type(models.TextChoices):
        Video = 'video' , 'Video'
        Audio = 'audio' , 'Audio'
        TextMessage = 'text_message' , 'Text Message'
    duration = models.IntegerField(default=30) # in minutes
    type = models.CharField(max_length=100 , choices= Type.choices)
    price = models.DecimalField(max_digits=10 , decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'type'],
                name='unique_doctor_session_type'
            )
        ]
# create the perscription then add the medications to it in the same request 
class Prescription(models.Model):
    patient = models.ForeignKey(Patient , on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE)
    appointment = models.OneToOneField(Appointment , on_delete=models.CASCADE , blank=True)
    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True , null=True)
    # يمكن أن يكون هناك أكثر من دواء في نفس الوصفة الطبية

class Medication(models.Model):
    prescription = models.ForeignKey(Prescription , on_delete=models.CASCADE , related_name='medications')

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True , null=True)
    side_effects = models.TextField(blank=True , null=True)

    # Usage instructions (optional)
    dosage_amount = models.IntegerField(blank=True , null=True)
    dosage_duration = models.IntegerField(blank=True , null=True) # in days
    dosage_interval = models.IntegerField(blank=True , null=True) # in hours

    def __str__(self):
        return self.name

class Payment(models.Model):
    class Status(models.TextChoices):
        Pending = 'pending', 'Pending'
        Completed = 'completed', 'Completed'
        Rejected = 'rejected', 'Rejected'
        Refunded = 'refunded', 'Refunded'
        
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='payment'
        )
    amount = models.DecimalField(max_digits=10 , decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=100)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.Pending)
    transaction_id = models.CharField(max_length=100 , blank=True , null=True)
    viewed_by = models.ManyToManyField(User, blank=True, related_name='viewed_payments')

    created_at = models.DateTimeField(auto_now_add=True)
