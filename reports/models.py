from django.db import models
from users.models import User

class AppReport(models.Model):
    """
    يتعامل مع الأخطاء التقنية، الاقتراحات، والملاحظات العامة حول التطبيق
    والتي يتم إرسالها من صفحة إعدادات التطبيق.
    """
    REPORT_TYPE_CHOICES = [
        ('BUG', 'Technical Bug / Error'),
        ('SUGGESTION', 'Suggestion / Improvement'),
        ('OTHER', 'Other Issues'),
    ]

    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='app_reports'
    )
    report_type = models.CharField(
        max_length=15, 
        choices=REPORT_TYPE_CHOICES, 
        default='BUG'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"App [{self.get_report_type_display()}] - {self.title}"


class UserReport(models.Model):
    """
    يتعامل مع البلاغات المتبادلة بين الأطباء والمرضى، سواء بعد الجلسات
    أو من خلال الملفات الشخصية. يتضمن حقول التحكم الإداري.
    """
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
    reported_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='received_user_reports'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # حقول التحكم الإداري
    action_taken = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES, 
        default='NONE'
    )
    admin_notes = models.TextField(
        blank=True, 
        null=True, 
        help_text="Internal notes written by the administrator regarding this action."
    )

    def __str__(self):
        author_name = self.author.username if self.author else "Deleted User"
        reported_name = self.reported_user.username if self.reported_user else "Deleted User"
        return f"Report by {author_name} against {reported_name}"