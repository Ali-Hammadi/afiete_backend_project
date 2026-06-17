from django.db import models
from django.utils import timezone
from users.models import User

class ReportStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    REVIEWED = 'reviewed', 'Reviewed'
    RESOLVED = 'resolved', 'Resolved'

class AppReport(models.Model):
    class ReportReason(models.TextChoices):
        APP_BUG = 'appBug', 'App Bug / Issue'
        CRASH_OR_FREEZE = 'crashOrFreeze', 'App Crashes or Freezes'
        PAYMENT_ISSUE = 'paymentIssue', 'Payment or Transaction Issue'
        OTHER = 'other', 'Other Issue'

    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='app_reports'
    )
    report_type = models.CharField(max_length=15, default='app')
    reason = models.CharField(max_length=30, choices=ReportReason.choices)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"App Report [{self.reason}] by {self.author.username}"


class UserReport(models.Model):
    class ReportType(models.TextChoices):
        DOCTOR = 'doctor', 'Doctor Report'
        SESSION = 'session', 'Session Report'

    class ReportReason(models.TextChoices):
        UNPROFESSIONAL = 'unprofessional', 'Unprofessional Behavior'
        HARASSMENT = 'harassment', 'Harassment'
        INAPPROPRIATE_CONTENT = 'inappropriateContent', 'Inappropriate Content'
        MISSING_APPOINTMENT = 'missingAppointment', 'Missing Appointment'
        OTHER = 'other', 'Other Issue'

    ACTION_CHOICES = [
        ('NONE', 'No Action Taken'),
        ('FUNDS_FROZEN', 'Financial Funds Frozen'),
        ('ACCOUNT_SUSPENDED', 'Account Temporarily Suspended'),
        ('ACCOUNT_DELETED', 'Account Permanently Deleted'),
        ('DISMISSED', 'Report Dismissed / Ignored'),
    ]

    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='submitted_user_reports'
    )
    report_type = models.CharField(max_length=15, choices=ReportType.choices)
    target_id = models.CharField(max_length=100, null=True, blank=True)  # يمثل الـ targetId (المستخدم أو الجلسة المشتكى عليها)
    target_name = models.CharField(max_length=255, null=True, blank=True) # اسم الهدف للتوثيق السريع
    reason = models.CharField(max_length=30, choices=ReportReason.choices)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    
    # حقول التحكم الإداري الخاصة بالباك آند
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='NONE')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"User Report [{self.report_type}] against {self.target_name or self.target_id}"