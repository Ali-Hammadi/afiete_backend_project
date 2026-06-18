from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Note(models.Model):
    NOTE_TYPE_CHOICES = [
        ('SESSION', 'Session Note'),
        ('PERSONAL', 'Personal Note'),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_notes'
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shared_notes'
    )
    content = models.TextField()
    note_type = models.CharField(max_length=10, choices=NOTE_TYPE_CHOICES, default='PERSONAL')
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note #{self.id} by {self.creator.username}"

    def save(self, *args, **kwargs):
            # التحقق الذكي باستخدام values_list الخفيف لتجنب الاستعلامات المكررة
            if self.pk:
                # جلب حالة الحقل is_shared كقيمة مباشرة وسريعة
                already_shared = Note.objects.filter(pk=self.pk).values_list('is_shared', flat=True).first()
                if already_shared and not self.is_shared:
                    # إذا كانت الملاحظة مشتركة مسبقاً وتم محاولة إلغاء المشاركة، يتم حذف البلاغات المتعلقة بها
                    from reports.models import AppReport  # استيراد محلي لتجنب التداخل الدائري
                    AppReport.objects.filter(target_id=self.pk, report_type='note').delete()
                    
            super().save(*args, **kwargs)