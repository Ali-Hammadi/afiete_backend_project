from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination

from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import AppointmentFilter

from .serializers import (PricesSerializer,
                          PaymentSerializer,
                          AppointmentSerializer,
                          AppointmentListSerializer,
                          RetrieveAppointmentSerializer,
                          RescheduleAppointmentSerializer,)
from .models import SessionPrice, Appointment, Payment
from users.permissions import IsDoctor, IsPatient

from django.shortcuts import get_object_or_404
class SessionPricesViewSet(viewsets.ModelViewSet):
    serializer_class = PricesSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    lookup_field = 'type'

    def get_queryset(self):
        return SessionPrice.objects.filter(doctor=self.request.user.doctor)


class BookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    def post(self, request):
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save() # 
            return Response({
                "message":"“Your reservation request has been submitted successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  

class PatientAppointmentListView(ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AppointmentFilter
    ordering_fields = ['date']
    pagination_class = PageNumberPagination
    pagination_class.page_size = 5

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.patient).order_by('-date')


class DoctorAppointmentListView(ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AppointmentFilter
    ordering_fields = ['date']

    pagination_class = PageNumberPagination
    pagination_class.page_size = 5

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.doctor).order_by('-date')
        
class CancelAppointmentView(UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient'):
            return Appointment.objects.filter(patient=user.patient)
        elif hasattr(user, 'doctor'):
            return Appointment.objects.filter(doctor=user.doctor)
        return Appointment.objects.none()

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        user = request.user

        if appointment.status in ['cancelled', 'expired', 'completed']:
            return Response(
                {"error": "Cannot cancel this appointment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if appointment.status == 'confirmed':
            if hasattr(appointment, 'payment'):
                appointment.payment.status = 'refunded'
                appointment.payment.save()
                appointment.cancelled_by = 'patient' if hasattr(user, 'patient') else 'doctor' 

        appointment.status = 'cancelled'
        appointment.save()

        return Response({"message": "Appointment cancelled successfully."})
class RetrieveAppointmentAPIView(RetrieveAPIView): 
    permission_classes = [IsAuthenticated, IsDoctor]
    serializer_class = RetrieveAppointmentSerializer
    lookup_field = 'pk'
    def get_queryset(self):
        return Appointment.objects.filter(
            doctor = self.request.user.doctor
        )

class RescheduleAppointmentView(UpdateAPIView):
    serializer_class = RescheduleAppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.patient)

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status not in ['pending', 'confirmed']:
            return Response(
                {"error": "Cannot reschedule this appointment."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
    
class CreatePaymentView(CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

class PaymentListView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient'):
            return Payment.objects.filter(appointment__patient=user.patient)
        elif hasattr(user, 'doctor'):
            return Payment.objects.filter(appointment__doctor=user.doctor)
        return Payment.objects.none()
