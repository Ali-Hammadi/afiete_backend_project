from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

# استيراد الموديلات من تطبيق الـ doctors
from .models import Doctor, Education, Schedule, SubSpecialization
from django.db.models import Max
# استيراد الموديلات من تطبيق الـ appointments (لأغراض الفلترة)
from appointments.models import SessionPrice
from users.permissions import IsAccountActiveAndUnfrozen
# استيراد السيريالايزرز
from .serializers import (
    DoctorRegisterSerializer,
    DoctorProfileSerialzer, 
    DoctorEducationSerializer,
    ScheduleSerializer,
    DoctorPublicProfileSerializer,
    AvailableSlotsSerializer,
    SubSpecializationSerializer
)

# استيراد الصلاحيات
from users.permissions import IsDoctor, IsVerified 

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------

class DoctorRegisterView(generics.CreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorRegisterSerializer

    @extend_schema(
        summary="Register a New Doctor Account",
        description="Creates a new doctor instance. The profile will initially be unverified and pending admin approval.",
        responses={
            201: OpenApiResponse(description="Doctor registered successfully. Activation required."),
            400: OpenApiResponse(description="Validation error with the submitted email or data.")
        }
    )
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({"message": "Doctor registered successfully", "is_verified": False}, status=201)


class DoctorProfileView(generics.RetrieveUpdateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorProfileSerialzer
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]
    def get_object(self):
        return self.request.user.doctor
        
    @extend_schema(
        summary="Update Authenticated Doctor Profile",
        description="Allows doctors to modify experience, bio, and multi-select sub-specialties.",
        request=DoctorProfileSerialzer,
        responses={
            200: OpenApiResponse(response=DoctorProfileSerialzer, description="Profile updated successfully."),
            400: OpenApiResponse(description="Bad Request."),
            401: OpenApiResponse(description="Unauthorized.")
        }
    )
    def update(self, request, *args, **kwargs):
        res = super().update(request, *args, **kwargs)
        return Response({
            "data": res.data,
            "message": "Doctor profile updated successfully"}, status=200)


# --- كلاس إدارة تعليم الطبيب ---
class DoctorEducationView(generics.CreateAPIView):
    serializer_class = DoctorEducationSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]

    def get_queryset(self):
        return Education.objects.filter(doctor=self.request.user.doctor)
    
    @extend_schema(
        summary="Add Education Certification",
        description="Allows a logged-in doctor to append an academic degree or certification to their history.",
        request=DoctorEducationSerializer,
        responses={201: OpenApiResponse(description="Doctor education added successfully.")}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(doctor=request.user.doctor)
        return Response({"message": "Doctor education added successfully"}, status=201)


class ScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]
    serializer_class = ScheduleSerializer

    def get_object(self):
        doctor = self.request.user.doctor
        id = self.kwargs.get(self.lookup_field)
        try:
            return Schedule.objects.get(id=id, doctor=doctor)
        except Schedule.DoesNotExist: 
            raise NotFound("Not found schedule")
            
    def get_queryset(self):
        day_of_week = self.request.query_params.get('day_of_week')
        doctor = self.request.user.doctor
        if not day_of_week: 
            return Schedule.objects.filter(doctor=doctor)
        return Schedule.objects.filter(day_of_week=day_of_week, doctor=doctor)

class AvailableSlotsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]

    @extend_schema(
        summary="Get Doctor Available Slots by Date",
        description="Returns an array of available booking hours based on the doctor's weekly work schedule.",
        parameters=[
            OpenApiParameter(name="date", type=str, location=OpenApiParameter.QUERY, description="Target date in YYYY-MM-DD format.")
        ]
    )
    def get(self, request, doctor_username):
        doctor = get_object_or_404(Doctor, user__username=doctor_username)
        serializer = AvailableSlotsSerializer(data=request.query_params)
        
        if serializer.is_valid():
            data_context = {
                'doctor': doctor,
                'date': serializer.validated_data['date']
            }
            final_serializer = AvailableSlotsSerializer(data_context)
            return Response(final_serializer.data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorPublicProfileView(generics.RetrieveAPIView): 
    queryset = Doctor.objects.all()
    serializer_class = DoctorPublicProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    lookup_field = 'doctor_username'

    def get_object(self):
        username_val = self.kwargs.get(self.lookup_field)
        doctor = get_object_or_404(Doctor, user__username=username_val)
        return doctor


class SubSpecializationListView(generics.ListAPIView):
    queryset = SubSpecialization.objects.all()
    serializer_class = SubSpecializationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]


class DoctorListView(generics.ListAPIView):
    """
    قائمة الأطباء المتاحين للمرضى بناءً على الشروط الصارمة:
    1. حالة الطبيب المقبول فقط (approved).
    2. يملك جلسات بأسعار حقيقية أكبر من صفر.
    3. قاعدة الـ 7 أيام: قام بتحديث أو تحديد مواعيده خلال الـ 7 أيام الماضية حصراً.
    """
    serializer_class = DoctorPublicProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['specialties']

    def get_queryset(self):
        # 1. البدء بالأطباء المقبولين فقط
        queryset = Doctor.objects.filter(status='approved')

        # 2. شرط أنواع الجلسات والأسعار (يجب أن يملك جلسة وسعرها أكبر من 0)
        queryset = queryset.filter(session_prices__price__gt=0)

        # 3. تطبيق قاعدة الـ 7 أيام (حساب وقت الفلترة بناءً على وقت الاستعلام الحالي)
        seven_days_ago = timezone.now() - timedelta(days=7)
        queryset = queryset.filter(schedules__updated_at__gte=seven_days_ago)

        # 4. منع تكرار الأطباء في الاستجابة (Distinct) لضمان أداء واجهات Flutter
        return queryset.distinct()