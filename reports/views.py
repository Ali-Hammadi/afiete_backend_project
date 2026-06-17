from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView
from django.utils import timezone
from assessments import serializers
from users.permissions import IsAccountActiveAndUnfrozen
from .models import AppReport, UserReport
from .serializers import AppReportSerializer, UserReportSerializer

class ReportConfigView(APIView):
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
    """إنشاء بلاغ سلوكي ضد مستخدم (طبيب) أو متعلق بجلسة معينة"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = UserReportSerializer

    def perform_create(self, serializer):
        # التحقق من عدم قيام المستخدم بالإبلاغ عن نفسه إذا كان الهدف مستخدم
        target_id = serializer.validated_data.get('target_id')
        report_type = serializer.validated_data.get('report_type')
        
        if report_type == 'doctor' and str(target_id) == str(self.request.user.id):
            raise serializers.ValidationError({"message": "You cannot report yourself."})
            
        serializer.save(author=self.request.user)


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