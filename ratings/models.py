from django.db import models
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
class Rating(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, default=None, null=True)
    rating = models.PositiveIntegerField()
    comment = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)