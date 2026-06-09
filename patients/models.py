from django.db import models
from users.models import User

class Patient(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    nickname = models.CharField(max_length=100 , blank=True , null=True)
    psychological_history = models.TextField(blank=True , null=True)