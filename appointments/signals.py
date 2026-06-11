from assessments.utils import enable_assessment_for_patient
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment

@receiver(post_save, sender=Appointment)
def trigger_assessment_on_session_end(sender, instance, created, **kwargs):
    """
    تفعيل التقييم النفسي للمريض فقط عند اكتمال الجلسة وعدم وجود جلسات قادمة.
    (تم تجريد هذه الدالة من أي تحويل مالي تلقائي لحماية الأموال)
    """
    if not created and instance.status == Appointment.Status.COMPLETED:
        # إذا انتهى الكورس العلاجي، نفعّل الاختبار التقييمي للمريض تلقائياً (منطق طبي فني وليس مالي)
        if instance.has_next_session is False:
            enable_assessment_for_patient(instance.patient)