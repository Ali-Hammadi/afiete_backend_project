from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Education, Doctor

@receiver(post_save, sender=Education)
def update_doctor_education_status(sender, instance, **kwargs):
    doctor = instance.doctor
    print(f"Education status for doctor {doctor.user.username} has been updated to {instance.status}.")
    if instance.status == 'approved':
        doctor.status = 'approved'
    elif instance.status == 'rejected':
        doctor.status = 'rejected'
    else:
        doctor.status = 'pending'
    doctor.save()