from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Appointment

@receiver(pre_save, sender=Appointment)
def auto_refund_on_missed_session(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = Appointment.objects.get(id=instance.id)
            # إذا تحولت الجلسة إلى "فائتة" ولم تكن كذلك من قبل
            if instance.status == Appointment.Status.Missed and old_instance.status != Appointment.Status.Missed:
                # التحقق من وجود عملية دفع مكتملة واسترجاعها
                if hasattr(instance, 'payment') and instance.payment.status == 'completed':
                    instance.payment.status = 'refunded'
                    instance.payment.save()
                    # توثيق أن النظام هو من ألغى الجلسة بسبب غياب الطبيب
                    instance.cancelled_by = "System (Doctor No-Show - Auto Refunded)"
        except Appointment.DoesNotExist:
            pass
        
        

from assessments.utils import enable_assessment_for_patient

@receiver(post_save, sender=Appointment)
def trigger_assessment_on_session_end(sender, instance, created, **kwargs):
    """
    Triggers an assessment activation when a session is completed 
    and no next session is planned.
    """
    if not created:
        if instance.status == Appointment.Status.Completed:
            # Trigger if patient explicitly states no next session
            if instance.has_next_session is False:
                enable_assessment_for_patient(instance.patient)