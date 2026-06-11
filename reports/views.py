from rest_framework import generics, permissions, response, serializers as drf_serializers
from users.models import User
from users.permissions import IsAccountActiveAndUnfrozen
from .models import AppReport, UserReport
from .serializers import AppReportSerializer, UserReportSerializer
from drf_spectacular.utils import extend_schema
class CreateAppReportView(generics.CreateAPIView):
    """إنشاء بلاغ تقني أو اقتراح خاص بالتطبيق"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = AppReportSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CreateUserReportView(generics.CreateAPIView):
    """إنشاء بلاغ سلوكي ضد مستخدم آخر (طبيب أو مريض)"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = UserReportSerializer

    def perform_create(self, serializer):
        user_id = self.kwargs.get('reported_user_id')
        
        # حماية أمنية: منع المستخدم من الإبلاغ عن نفسه
        if user_id == self.request.user.id:
            raise drf_serializers.ValidationError({"message": "You cannot report yourself."})
            
        try:
            reported_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise drf_serializers.ValidationError({"message": "Target user does not exist."})
            
        serializer.save(author=self.request.user, reported_user=reported_user)


class MyReportsListView(generics.GenericAPIView):
    """عرض السجل الكامل لجميع ريبورتات المستخدم السابقة (تطبيق + مستخدمين) في واجهة واحدة"""
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    
    def get(self, request, *args, **kwargs):
        app_reports = AppReport.objects.filter(author=request.user).order_by('-created_at')
        user_reports = UserReport.objects.filter(author=request.user).order_by('-created_at')
        
        return response.Response({
            "app_reports": AppReportSerializer(app_reports, many=True).data,
            "user_reports": UserReportSerializer(user_reports, many=True).data
        })