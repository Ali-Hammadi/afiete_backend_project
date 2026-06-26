from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAccountActiveAndUnfrozen, IsPatient
from .models import Prescription
from .permissions import IsPrescribingDoctor
from .serializers import (
    DoctorPrescriptionCreateSerializer,
    DoctorPrescriptionUpdateSerializer,
    PrescriptionReadSerializer,
)


class PrescriptionQuerysetMixin:
    serializer_class = PrescriptionReadSerializer

    def base_queryset(self):
        return Prescription.objects.select_related(
            'doctor',
            'doctor__user',
            'patient',
            'patient__user',
            'appointment',
        ).prefetch_related('medications')


class DoctorPrescriptionCreateView(generics.CreateAPIView):
    serializer_class = DoctorPrescriptionCreateSerializer
    permission_classes = [IsAuthenticated, IsPrescribingDoctor, IsAccountActiveAndUnfrozen]


class DoctorPrescriptionListView(PrescriptionQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsPrescribingDoctor, IsAccountActiveAndUnfrozen]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()
        return self.base_queryset().filter(doctor=self.request.user.doctor)


class DoctorPrescriptionDetailView(PrescriptionQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsPrescribingDoctor, IsAccountActiveAndUnfrozen]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()
        return self.base_queryset().filter(doctor=self.request.user.doctor)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return DoctorPrescriptionUpdateSerializer
        return PrescriptionReadSerializer


class PatientPrescriptionListView(PrescriptionQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()
        return self.base_queryset().filter(patient=self.request.user.patient)


class PatientPrescriptionDetailView(PrescriptionQuerysetMixin, generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Prescription.objects.none()
        return self.base_queryset().filter(patient=self.request.user.patient)
