from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from users.permissions import IsAccountActiveAndUnfrozen
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from django.db.models import Sum
from decimal import Decimal
from rest_framework import generics, status, permissions
from django.utils import timezone
from django.db import transaction
from assessments.models import AssessmentResult
from assessments.utils import grant_doctor_access_to_assessment
from users.permissions import IsPatient, IsDoctor

from .models import Appointment, SessionPrice, Payment
from .filters import AppointmentFilter
from .serializers import (
    PricesSerializer,
    PaymentSerializer,
    AppointmentSerializer,
    AppointmentListSerializer,
    RetrieveAppointmentSerializer,
    RescheduleAppointmentSerializer,
    PastAppointmentSerializer,
    PatientUpdateNextSessionSerializer
)
from users.permissions import IsDoctor, IsPatient

class AppointmentPagination(PageNumberPagination):
    page_size = 5


# --- تعديل الأسعار: منع الحذف تماماً وتحويلها إلى Generics منيعة ---
class SessionPricesListCreateView(ListCreateAPIView):
    """Each doctor views and creates their own pricing schedules exclusively."""
    serializer_class = PricesSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return SessionPrice.objects.filter(doctor=self.request.user.doctor)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor)


class SessionPricesRetrieveUpdateView(RetrieveUpdateAPIView):
    """Each doctor views details and updates their pricing schedules without delete permissions."""
    serializer_class = PricesSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    lookup_field = 'type'

    def get_queryset(self):
        return SessionPrice.objects.filter(doctor=self.request.user.doctor)


class BookAppointmentView(APIView):
    """Allows patient to prepare an appointment request (Starts at 'pending')."""
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    serializer_class = AppointmentSerializer
    
    def post(self, request):
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save() 
            return Response({
                "message": "Your reservation request has been submitted successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  


class PatientAppointmentListView(ListAPIView):
    """Patients see only their own appointments."""
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AppointmentFilter
    ordering_fields = ['date']
    pagination_class = AppointmentPagination

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.patient).order_by('-date')


class PatientPastAppointmentsListView(ListAPIView):
    """Returns only past/inactive records belonging to the authenticated patient."""
    serializer_class = PastAppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    pagination_class = AppointmentPagination

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user.patient,
            status__in=['completed', 'cancelled', 'expired']
        ).order_by('-date')


class DoctorAppointmentListView(ListAPIView):
    """Doctors see only appointments booked with them."""
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AppointmentFilter
    ordering_fields = ['date']
    pagination_class = AppointmentPagination

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.doctor).order_by('-date')
        

class CancelAppointmentView(UpdateAPIView):
    # تعديل الصلاحية لتصبح حصراً للمريض لمنع الطبيب من استخدام الرابط نهائياً
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    
    def get_queryset(self):
        # البحث محصور فقط بمواعيد المريض المسجل حالياً لضمان عزل البيانات الكامل
        return Appointment.objects.filter(patient=self.request.user.patient)
        
    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        
        # منع إلغاء المواعيد المنتهية أو الملغاة بالفعل
        if appointment.status in ['completed', 'expired', 'cancelled']:
            return Response({"error": "You can't cancel ended or expired or canceled appointments."}, status=status.HTTP_400_BAD_REQUEST)
            
        # عملية الإلغاء وتوثيق الفاعل
        appointment.status = 'cancelled'
        appointment.cancelled_by = str(request.user.username)
        appointment.save()
        
        # في حال وجود دفع مسبق، يتم إرجاعه تلقائياً مالياً في النظام
        if hasattr(appointment, 'payment'):
            payment = appointment.payment
            payment.status = 'refunded'
            payment.save()
            
        return Response({"message": "Appointment cancelled successfully.", "status": "cancelled"}, status=status.HTTP_200_OK)


class RetrieveAppointmentAPIView(RetrieveAPIView): 
    """Restricts profile views to explicitly assigned doctor or patient accounts."""
    permission_classes = [IsAuthenticated]
    serializer_class = RetrieveAppointmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'doctor'):
            return Appointment.objects.filter(doctor=user.doctor)
        elif hasattr(user, 'patient'):
            return Appointment.objects.filter(patient=user.patient)
        return Appointment.objects.none()


class RescheduleAppointmentView(UpdateAPIView):
    """Changes dates/times using fully nested schedule collision validators."""
    serializer_class = RescheduleAppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.patient)

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status not in ['pending', 'confirmed']:
            return Response(
                {"error": "Cannot reschedule an appointment in its current state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        response = super().update(request, *args, **kwargs)
        appointment.status = 'confirmed'
        appointment.save()
        return response



class CreatePaymentView(CreateAPIView):
    """Charges the patient based on live doctor tariff tables and activates bookings."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsPatient]


class PaymentListView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AppointmentPagination
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient'):
            return Payment.objects.filter(appointment__patient=user.patient)
        elif hasattr(user, 'doctor'):
            return Payment.objects.filter(appointment__doctor=user.doctor)
        return Payment.objects.none()


class DoctorWalletView(APIView):
    """واجهة برمجية ليعرف الطبيب عبر Flutter إجمالي أرباحه والمبالغ المعلقة والمستلمة"""
    permission_classes = [IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]

    def get(self, request):
        doctor = request.user.doctor
        doctor_payments = Payment.objects.filter(appointment__doctor=doctor, status='completed')       
        total_earnings = doctor_payments.aggregate(Sum('doctor_amount'))['doctor_amount__sum'] or Decimal('0.00')
        transferred_amount = doctor_payments.filter(is_transferred_to_doctor=True).aggregate(Sum('doctor_amount'))['doctor_amount__sum'] or Decimal('0.00')
        
        pending_clearance = total_earnings - transferred_amount

        return Response({
            "total_earnings": total_earnings,          
            "transferred_amount": transferred_amount,  
            "pending_clearance": pending_clearance      
        }, status=status.HTTP_200_OK)
        
# ==================== 1. جلب الجلسات الفائتة للمريض ====================
class PatientMissedSessionsListView(ListAPIView):
    """عرض قائمة الجلسات الفائتة التي تخلف عنها المريض الحالي"""
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Appointment.objects.filter(
            patient=self.request.user.patient,
            status=Appointment.Status.Missed
        ).order_by('-date')


# ==================== 2. جلب الجلسات الفائتة للطبيب ====================
class DoctorMissedSessionsListView(ListAPIView):
    """عرض قائمة الجلسات الفائتة الخاصة بمراجعي الطبيب الحالي"""
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return Appointment.objects.filter(
            doctor=self.request.user.doctor,
            status=Appointment.Status.Missed
        ).order_by('-date')


# ==================== 3. استرداد الأموال (Refund) ====================
class RefundAppointmentView(APIView):
    """تحويل حالة الدفع للموعد الفائت إلى المسترد (refunded) وإلغاء الجلسة ماليًا"""
    permission_classes = [permissions.IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]

    def post(self, request, appointment_id):
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id, 
            patient=request.user.patient,
            status=Appointment.Status.Missed
        )
        
        payment = get_object_or_404(Payment, appointment=appointment)
        
        if payment.status == 'refunded':
            return Response({"detail": "تمت عملية استرداد أموال هذه الجلسة مسبقاً."}, status=status.HTTP_400_BAD_REQUEST)
            
        if payment.status != 'completed':
            return Response({"detail": "لا يمكن استرداد مبالغ لعمليات دفع غير مكتملة."}, status=status.HTTP_400_BAD_REQUEST)

        # تحويل الحالات برمجياً وحفظها بأمان
        payment.status = 'refunded'
        payment.save()
        
        appointment.status = Appointment.Status.Cancelled
        appointment.cancelled_by = "Patient (Refunded)"
        appointment.save()

        return Response({
            "message": "تم استرداد المبلغ بنجاح وتحديث المحفظة.",
            "appointment_id": appointment.id,
            "payment_status": payment.status
        }, status=status.HTTP_200_OK)


# ==================== 4. إعادة الجدولة (Reschedule) ====================
class RescheduleAppointmentView(UpdateAPIView):
    """إعادة جدولة الموعد (المؤكد أو الفائت) لتاريخ ووقت جديدين"""
    queryset = Appointment.objects.all()
    serializer_class = RescheduleAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_object(self):
        return get_object_or_404(Appointment, pk=self.kwargs.get('pk'), patient=self.request.user.patient)

    def perform_update(self, serializer):
        # عند إعادة الحجز بنجاح تعود حالة الموعد مؤكدة بالتاريخ الجديد مباشرة
        serializer.save(status=Appointment.Status.Confirmed, updated_at=timezone.now())


# ==================== 5. تحديث الكورس العلاجي بواسطة المريض ====================
class PatientUpdateNextSessionView(UpdateAPIView):
    """
    واجهة مخصصة تمنح المريض (وليس الطبيب) الأحقية في تحديد ما إذا كان بحاجة
    إلى جلسة قادمة (has_next_session = True/False) بعد انتهاء الجلسة أو تفويتها.
    """
    serializer_class = PatientUpdateNextSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_object(self):
        # التحقق من أن الموعد يخص المريض الحالي حصراً حمايةً للبيانات
        return get_object_or_404(Appointment, pk=self.kwargs.get('pk'), patient=self.request.user.patient)
    
 # ==================== ➕ Smart Review & Treatment Course Logic (English Responses) ====================

class BookAppointmentView(CreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def perform_create(self, serializer):
        # Save the appointment first
        appointment = serializer.save(patient=self.request.user.patient)
        
        # Check for the latest assessment result for this patient
        latest_assessment = AssessmentResult.objects.filter(
            patient=self.request.user.patient
        ).order_by('-created_at').first()

        # If found, share access with the new doctor
        if latest_assessment:
            grant_doctor_access_to_assessment(
                doctor=appointment.doctor, 
                assessment=latest_assessment
            )

@staff_member_required         
def financial_dashboard(request):
    now = timezone.now()
    periods = {
        'Daily': now - timedelta(days=1),
        'Weekly': now - timedelta(weeks=1),
        'Monthly': now - timedelta(days=30),
        'Yearly': now - timedelta(days=365)
    }

    stats = {}
    for label, start_date in periods.items():
        queryset = Payment.objects.filter(date__gte=start_date, status='completed')
        stats[label] = {
            'total_volume': queryset.aggregate(Sum('amount'))['amount__sum'] or 0,
            'admin_profit': queryset.aggregate(Sum('admin_commission'))['admin_commission__sum'] or 0,
            'doctors_payout': queryset.aggregate(Sum('doctor_amount'))['doctor_amount__sum'] or 0
        }

    return render(request, 'admin/financial_dashboard.html', {'stats': stats})