from django.urls import path
from .views import (DoctorRegisterView,
                    DoctorProfileView,
                    DoctorEducationView,
                    AvailableSlotsView,
                    DoctorPublicProfileView,
                    SubSpecializationListView,
                    DoctorListView
                    )

urlpatterns = [
    # رابط جلب كل الأطباء وفلترتهم للمريض
    path('', DoctorListView.as_view(), name='doctor-list'),
    
    path('register/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('profile/', DoctorProfileView.as_view(), name="Doctor-profile"),
    
    # رابط جلب التخصصات الـ 11
    path('specialties/', SubSpecializationListView.as_view(), name='specialties-list'),
    
    path('education/add', DoctorEducationView.as_view(), name="Doctor-education-add"),
    path('<str:doctor_username>/available-slots/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('<str:doctor_username>/profile/public', DoctorPublicProfileView.as_view(), name='doctor-profile-public'),
]