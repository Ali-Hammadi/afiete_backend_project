from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorNoteViewSet, PatientNoteViewSet

# 1. Router for Patient Gateway
patient_router = DefaultRouter()
patient_router.register(r'', PatientNoteViewSet, basename='patient-notes')

# 2. Router for Doctor Gateway
doctor_router = DefaultRouter()
doctor_router.register(r'', DoctorNoteViewSet, basename='doctor-notes')

urlpatterns = []