from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta, date
# User -> patiant 
# User -> doctor 
# User -> Admin


class User(AbstractUser):
    
    class Gender (models.TextChoices):
        Male = 'male' , 'Male'
        Female = 'female' , 'Female'
    class Status (models.TextChoices):
        Active = 'active' , 'Active'
        Deactive = 'deactive' , 'Deactive'
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15 , blank=True , null=True)
    birth_date = models.DateField(blank=True , null=True)

    gender = models.CharField(max_length=100 , choices=  Gender.choices , null= True , blank=True)
    status = models.CharField(max_length=100 , choices= Status.choices , default=Status.Active)
    
    is_verified =   models.BooleanField(default=False) # to check if the user has verified his email or not
    # otp_code = models.CharField(max_length=6 , blank=True , null=True) # to store the OTP code for email verification
    can_reset_password = models.BooleanField(default=False)
    is_funds_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = date.today()
        if self.birth_date: 
            return today.year - self.birth_date.year - ((today.month, today.day) < 
                                                        (self.birth_date.month, self.birth_date.day) )
        return None
class notes(models.Model):
    Author = models.ForeignKey(User , on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

def otp_expiry():
    return timezone.now() + timedelta(minutes=10)
class Otp(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    code = models.CharField(max_length=120)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=otp_expiry) # OTP expires after 10 minutes

    def generate_otp():
        from random import randint
        return str(randint(1000, 9999))