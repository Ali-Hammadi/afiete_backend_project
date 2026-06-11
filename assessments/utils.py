# assessments/utils.py
from django.utils import timezone
from django.db import transaction
# استبدل هذه الاستيرادات بمسارات الموديلات الصحيحة لديك
from .models import PatientAssessmentProfile, AssessmentAccess

def enable_assessment_for_patient(patient):
    """
    Function to enable the assessment for a specific patient.
    This creates or updates a profile to allow the patient to take a new test.
    """
    with transaction.atomic():
        # البحث عن ملف المريض الخاص بالاختبارات أو إنشاؤه
        profile, created = PatientAssessmentProfile.objects.get_or_create(
            patient=patient
        )
        
        # تفعيل خاصية إجراء الاختبار
        profile.can_take_assessment = True
        profile.last_enabled_at = timezone.now()
        profile.save()
        
    return True

def grant_doctor_access_to_assessment(doctor, assessment_result):
    """
    Function to grant a doctor access to a specific patient's assessment result.
    This creates an access record linking the doctor to the assessment result.
    """
    with transaction.atomic():
        # إنشاء أو تحديث سجل الوصول للطبيب
        access, created = AssessmentAccess.objects.update_or_create(
            doctor=doctor,
            assessment_result=assessment_result,
            defaults={
                'granted_at': timezone.now(),
                'is_active': True
            }
        )
        
    return True