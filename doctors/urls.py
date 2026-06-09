from django.urls import path
from .views import (DoctorRegisterView,
                    DoctorProfileView,
                    DoctorEducationView,
                    AvailableSlotsView,
                    DoctorPublicProfileView
                    )
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('register/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('profile/', DoctorProfileView.as_view(), name="Doctor-profile"),
    path('education/add', DoctorEducationView.as_view(), name="Doctor-education-add"),

    path('<str:doctor_username>/available-slots/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('<str:doctor_username>/profile/public', DoctorPublicProfileView.as_view(), name='doctor-profile-public'),
]