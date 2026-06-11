from django.urls import path
from .views import DoctorRetrievePatientView

urlpatterns = [
    path('view/<int:pk>/', DoctorRetrievePatientView.as_view(), name='doctor-get-patient-profile'),
]