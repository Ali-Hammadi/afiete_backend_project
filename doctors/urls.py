from django.urls import path
from .views import (
    DoctorRegisterView, DoctorProfileView, DoctorEducationView,
    AvailableSlotsView, DoctorPublicProfileView, SubSpecializationListView,
    DoctorListView
)

urlpatterns = [
    # --- تستدعى من بوابة المريض (api/patient/doctors/) ---
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('specialties/', SubSpecializationListView.as_view(), name='specialties-list'),
    path('<str:doctor_username>/available-slots/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('<str:doctor_username>/profile/public/', DoctorPublicProfileView.as_view(), name='doctor-profile-public'),

    # --- تستدعى من بوابة الطبيب (api/doctor/) ---
    path('register/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('profile/', DoctorProfileView.as_view(), name="doctor-profile"),
    path('education/add/', DoctorEducationView.as_view(), name="doctor-education-add"),
    
    # نصيحة: الـ ViewSets المتبقية (ScheduleViewSet) يفضل وضع روابطها هنا كـ مسار عادي 
    # مثل: path('schedule/', ScheduleViewSet.as_view({'get': 'list', 'post': 'create'})) بدلاً من الـ Router المعقد في الملف الرئيسي.
]