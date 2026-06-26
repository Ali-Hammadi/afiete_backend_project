from django.urls import path
from .views import (
    DoctorPrescriptionCreateView,
    DoctorPrescriptionDetailView,
    DoctorPrescriptionListView,
)

urlpatterns = [
    path('create/', DoctorPrescriptionCreateView.as_view(), name='doctor-prescription-create'),
    path('', DoctorPrescriptionListView.as_view(), name='doctor-prescription-list'),
    path('<int:pk>/', DoctorPrescriptionDetailView.as_view(), name='doctor-prescription-detail'),
]