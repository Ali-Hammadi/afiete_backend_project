from rest_framework import generics, permissions, response, status
from rest_framework.exceptions import ValidationError
from django.db.models import Q  # مخصصة للاستعلامات المركبة (OR)
from django.utils import timezone
from appointments.models import Appointment
from users.permissions import IsAccountActiveAndUnfrozen
from .models import AppReport, UserReport
from .serializers import AppReportSerializer, UserReportSerializer

# ⚠️ قم باستيراد موديل الـ Appointment من التطبيق الخاص به في مشروعك، على سبيل المثال:
# from appointments.models import Appointment


class ReportConfigView(generics.GenericAPIView):
    """إرجاع الإعدادات والأنواع الأساسية للريبورتات ليتم استهلاكها ديناميكياً في التطبيق"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        config_data = {
            "reportTypes": ["doctor", "session", "app"],
            "reasons": {
                "app": [
                    {"key": "appBug", "label": "Technical Bug / Error"},
                    {"key": "crashOrFreeze", "label": "App Crashes or Freezes"},
                    {"key": "paymentIssue", "label": "Payment or Transaction Issue"},
                    {"key": "other", "label": "Other Issues"}
                ],
                "user": [
                    {"key": "unprofessional", "label": "Unprofessional Behavior"},
                    {"key": "harassment", "label": "Harassment"},
                    {"key": "inappropriateContent", "label": "Inappropriate Content"},
                    {"key": "missingAppointment", "label": "Missing Appointments"},
                    {"key": "other", "label": "Other Issues"}
                ]
            }
        }
        return response.Response(config_data, status=status.HTTP_200_OK)


class CreateAppReportView(generics.CreateAPIView):
    """إنشاء بلاغ خاص بالتطبيق"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = AppReportSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, report_type='app')


class CreateUserReportView(generics.CreateAPIView):
    """إنشاء بلاغ سلوكي ضد مستخدم آخر (سواء كان طبيب أو مريض) أو متعلق بجلسة معينة"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = UserReportSerializer

    def perform_create(self, serializer):
        user = self.request.user
        target_id = serializer.validated_data.get('target_id')
        report_type = serializer.validated_data.get('report_type')
        
        # 1. منع المستخدم من الإبلاغ عن نفسه كإجراء حماية أمني
        if report_type == 'doctor' and str(target_id) == str(user.id):
            raise ValidationError({"message": "You cannot report yourself."})
            
        # 2. إذا كان البلاغ موجه ضد مستخدم (من الملف الشخصي للطبيب أو العكس)
        if report_type == 'doctor':
            # نتحقق من وجود أي موعد يربط بين المستخدم الحالي والمستخدم المستهدف (target_id)
            # ملاحظة: الكود يفترض أن موديلي Patient و Doctor يرتبطان بـ User عبر حقل اسمه 'user'
            has_appointment = Appointment.objects.filter(
                Q(patient__user=user, doctor__user_id=target_id) | 
                Q(doctor__user=user, patient__user_id=target_id)
            ).exists()
            
            if not has_appointment:
                raise ValidationError({
                    "message": "You cannot report this user because there is no shared appointment history between you."
                })
                
        # 3. إذا كان البلاغ موجه ضد جلسة/موعد معين (بعد انتهائه مثلاً)
        elif report_type == 'session':
            try:
                # جلب الموعد باستخدام المعرف الممرر في الـ targetId
                appointment = Appointment.objects.get(pk=target_id)
                
                # التحقق من أن المستخدم الحالي هو فعلياً طرف في هذا الموعد (إما المريض أو الطبيب)
                if appointment.patient.user != user and appointment.doctor.user != user:
                    raise ValidationError({
                        "message": "You cannot report this session because you are not a participant in it."
                    })
            except Appointment.DoesNotExist:
                raise ValidationError({"message": "The specified appointment does not exist."})

            # في حال نجاح التحقق، يمكن توثيق اسم الهدف تلقائياً كـ target_name للسهولة في لوحة التحكم
            serializer.validated_data['target_name'] = f"Appointment #{appointment.id} ({appointment.type})"

        # حفظ البلاغ في قاعدة البيانات بعد اجتياز جميع الشروط
        serializer.save(author=user)


class MyReportsListView(generics.GenericAPIView):
    """عرض سجل ريبورتات المستخدم الحالية بكافة أنواعها"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    
    def get(self, request, *args, **kwargs):
        app_reports = AppReport.objects.filter(author=request.user).order_by('-created_at')
        user_reports = UserReport.objects.filter(author=request.user).order_by('-created_at')
        
        return response.Response({
            "app_reports": AppReportSerializer(app_reports, many=True).data,
            "user_reports": UserReportSerializer(user_reports, many=True).data
        })