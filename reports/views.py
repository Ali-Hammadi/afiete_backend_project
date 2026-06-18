from rest_framework import generics, permissions, response, status, serializers as drf_serializers
from rest_framework.exceptions import ValidationError
from django.db.models import Q  # مخصصة للاستعلامات المركبة (OR / AND)
from users.permissions import IsAccountActiveAndUnfrozen
from appointments.models import Appointment  # استيراد موديل المواعيد للتحقق من الجلسات المشتركة
from .models import AppReport, UserReport
from .serializers import AppReportSerializer, UserReportSerializer

# أدوات مكتبة drf-spectacular لتوثيق السواجر المشترك وتجنب التوليد العشوائي
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.serializers import Serializer

class EmptySerializer(Serializer):
    pass

class ReportConfigView(generics.GenericAPIView):
    """إرجاع الإعدادات والأنواع الأساسية للريبورتات ليتم استهلاكها ديناميكياً في التطبيق (مشترك)"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get reports configuration and reasons mapping",
        description="Returns available report categories and reasons for both Patient and Doctor applications.",
        responses={
            200: inline_serializer(
                name='ReportConfigResponse',
                fields={
                    'reportTypes': drf_serializers.ListField(child=drf_serializers.CharField()),
                    'reasons': inline_serializer(
                        name='ReportReasonsMap',
                        fields={
                            'app': drf_serializers.ListField(child=drf_serializers.DictField()),
                            'user': drf_serializers.ListField(child=drf_serializers.DictField()),
                        }
                    )
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        config_data = {
            "reportTypes": ["user", "app"],
            "reasons": {
                "app": [
                    {"key": "BUG", "label": "Technical Bug / Error"},
                    {"key": "SUGGESTION", "label": "Suggestion / Improvement"},
                    {"key": "OTHER", "label": "Other Issues"}
                ],
                "user": [
                    {"key": "unprofessional", "label": "Unprofessional Behavior / معاملة غير مهنية"},
                    {"key": "harassment", "label": "Harassment / إساءة أو تحرش"},
                    {"key": "inappropriateContent", "label": "Inappropriate Content / محتوى غير لائق"},
                    {"key": "missingAppointment", "label": "Missing Appointments / عدم الحضور للموعد"},
                    {"key": "other", "label": "Other Issues / أسباب أخرى"}
                ]
            }
        }
        return response.Response(config_data, status=status.HTTP_200_OK)


class CreateAppReportView(generics.CreateAPIView):
    """إنشاء بلاغ تقني أو اقتراح خاص بالتطبيق (متاح للمريض والطبيب)"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = AppReportSerializer

    def perform_create(self, serializer):
        # يتم حفظ البلاغ وربطه بالمستخدم الحالي تلقائياً سواء كان مريض أو طبيب
        serializer.save(author=self.request.user)


class CreateUserReportView(generics.CreateAPIView):
    """إنشاء بلاغ سلوكي ضد مستخدم آخر بشرط وجود تاريخ جلسات مشترك بينهما"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = UserReportSerializer

    def perform_create(self, serializer):
        user = self.request.user
        reported_user = serializer.validated_data.get('reported_user')
        
        # 1. حماية أمنية: منع المستخدم من الإبلاغ عن نفسه
        if reported_user == user:
            raise ValidationError({"message": "You cannot report yourself."})
            
        # 2. التحقق الذكي من الجلسات المشتركة:
        # نبحث في جدول المواعيد للتأكد من وجود موعد يجمع بين هذا المستخدم والمستخدم المشتكى عليه
        # الشرط يغطي الحالتين (المشتكي مريض والمشتكى عليه طبيب، أو المشتكي طبيب والمشتكى عليه مريض)
        shared_session_exists = Appointment.objects.filter(
            Q(patient__user=user, doctor__user=reported_user) | 
            Q(doctor__user=user, patient__user=reported_user)
        ).exists()
        
        if not shared_session_exists:
            raise ValidationError({
                "message": "You cannot report this user because there is no shared appointment/session history between you."
            })
            
        # 3. حفظ البلاغ إذا اجتاز التحقق بنجاح
        serializer.save(author=user)


class MyReportsListView(generics.GenericAPIView):
    """عرض السجل الكامل لجميع ريبورتات المستخدم الحالي فقط (سواء كان طبيب أو مريض)"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    
    @extend_schema(
        summary="Get current user history of submitted reports",
        description="Returns lists of reports created by the currently authenticated user (Patient or Doctor).",
        responses={
            200: inline_serializer(
                name='MyReportsListResponse',
                fields={
                    'app_reports': AppReportSerializer(many=True),
                    'user_reports': UserReportSerializer(many=True),
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        # الفلترة هنا تتم بـ author=request.user، وهي تضمن بشكل صارم جداً أن كل يوزر يرى بلاغاته هو فقط
        app_reports = AppReport.objects.filter(author=request.user).order_by('-created_at')
        user_reports = UserReport.objects.filter(author=request.user).order_by('-created_at')
        
        return response.Response({
            "app_reports": AppReportSerializer(app_reports, many=True).data,
            "user_reports": UserReportSerializer(user_reports, many=True).data
        })