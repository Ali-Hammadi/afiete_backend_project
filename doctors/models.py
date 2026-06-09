from django.db import models
from users.models import User
from assessments.models import QuestionGroup
# Create your models here.

class Job_title(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class SubSpecialization(models.Model):
    name           = models.CharField(max_length=255, default='')  # ← مو blank/null
    question_group = models.ForeignKey(
        QuestionGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subspecializations'
        , default=None
    )
    def __str__(self):
        return self.name
    
class Doctor(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE)
    job_title = models.ForeignKey(Job_title, on_delete=models.SET_NULL, null=True, blank=True)
    bio = models.TextField(blank=True , null=True)
    experience = models.IntegerField(blank=True , null=True)
    
    STATUS_CHOICES = [ 
        ('pending', 'Pending'),
        ('approved', 'Approved'), 
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') # to track the approval status of the doctor
    photo = models.ImageField(upload_to='media/doctor_photos/%Y/%m/%d/', blank=True , null=True) # to allow doctors to upload their photos
    specialties = models.ManyToManyField(SubSpecialization)
    def __str__(self):
        return self.user.username
    
    @property 
    def specialization_list(self):
        specs = self.specialties.all()
        objs = []
        for spec in specs: 
            objs.append(spec.name)
        return objs
    
    @property
    def average_rating(self):
        from ratings.models import Rating
        ratings = Rating.objects.filter(appointment__doctor=self)
        
        average = ratings.aggregate(models.Avg('rating'))['rating__avg']
        
        return round(average, 1) if average is not None else 0.0
    
    @property
    def patients_count(self):
        from appointments.models import Appointment
        
        count = Appointment.objects.filter(doctor=self).exclude(status='cancelled').values('patient').distinct().count()
        
        return count
class Education(models.Model):
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE , related_name='educations')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField(blank=True , null=True)
    license_number = models.CharField(max_length=100 , blank=True , null=True)
    brief_description = models.TextField(blank=True , null=True)
    
    certificate = models.FileField(upload_to=f'media/certificates/%Y/%m/%d/', blank=True , null=True) # to allow doctors to upload their certificates or licenses
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') # to track the approval status of the education record
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # to track when the education record
   
    reveiwed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='education_reviews') # to track which admin reviewed the education record
    reveiwed_at = models.DateTimeField(blank=True , null=True) # to track when the education record was reviewed7
    reveiwer_comment = models.TextField(blank=True , null=True) # to allow the admin to add comments when reviewing the education record
    def __str__(self):
        return f"{self.doctor.user.username} - {self.degree}"

# اوقات الدوام للأطباء
class Schedule(models.Model):
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE , related_name='schedules')
    DAYS_OF_WEEK = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    )
    day_of_week = models.CharField(max_length=20, choices=DAYS_OF_WEEK) # e.g., Monday, Tuesday, etc.
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # to track when the schedule was last updated
    # يمكن أن يكون هناك أكثر من توقيت في نفس اليوم لنفس الطبيب
    
    def __str__(self):
        return f"{self.doctor.user.username} - {self.day_of_week} ({self.start_time} - {self.end_time})"
class PaymentMethod(models.Model):
    doctor = models.ForeignKey(Doctor , on_delete=models.CASCADE , related_name='payment_methods')
    method = models.CharField(max_length=100) # e.g., Credit Card, PayPal, etc.

    is_active = models.BooleanField(default=True) # to allow doctors to activate or deactivate payment methods without deleting them
    details = models.TextField(blank=True , null=True) # to store any additional details related to the payment method (e.g., account number, etc.)