from django.urls import path
from .views import PatientPrescriptionDetailView, PatientPrescriptionListView

urlpatterns = [
    path('', PatientPrescriptionListView.as_view(), name='patient-prescription-list'),
    path('<int:pk>/', PatientPrescriptionDetailView.as_view(), name='patient-prescription-detail'),
]