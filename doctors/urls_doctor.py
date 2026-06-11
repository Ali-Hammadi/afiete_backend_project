from django.urls import path
from .views import DoctorRegisterView, DoctorProfileView, DoctorEducationView, ScheduleViewSet

urlpatterns = [
    path('register/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('profile/', DoctorProfileView.as_view(), name="doctor-profile"),
    path('education/add/', DoctorEducationView.as_view(), name="doctor-education-add"),
    path('schedule/', ScheduleViewSet.as_view({'get': 'list', 'post': 'create'}), name='doctor-schedule-list'),
    path('schedule/<int:pk>/', ScheduleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='doctor-schedule-detail'),
]