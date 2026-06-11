from rest_framework import generics, permissions, response
from musics.models import User
from users.permissions import IsAccountActiveAndUnfrozen
from .models import AppReport, UserReport
from .serializers import AppReportSerializer, UserReportSerializer

class CreateAppReportView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = AppReportSerializer
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CreateUserReportView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = UserReportSerializer
    def perform_create(self, serializer):
        user_id = self.kwargs.get('reported_user_id')
        reported_user = User.objects.get(pk=user_id)
        serializer.save(author=self.request.user, reported_user=reported_user)

class MyReportsListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    
    def get(self, request):
        app_reports = AppReport.objects.filter(author=request.user).order_by('-created_at')
        user_reports = UserReport.objects.filter(author=request.user).order_by('-created_at')
        
        return response.Response({
            "app_reports": AppReportSerializer(app_reports, many=True).data,
            "user_reports": UserReportSerializer(user_reports, many=True).data
        })