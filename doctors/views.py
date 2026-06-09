from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response 
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample

from .models import Doctor, Education, Schedule, SubSpecialization
from .serializers import (DoctorRegisterSerializer,
                          DoctorProfileSerialzer, 
                          DoctorEducationSerializer,
                          ScheduleSerializer,
                          DoctorPublicProfileSerializer,
                          AvailableSlotsSerializer,
                          SubSpecializationSerializer)
from users.permissions import IsDoctor, IsVerified 

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
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get_object(self):
        return self.request.user.doctor
        
    @extend_schema(
        summary="Update Authenticated Doctor Profile",
        description="Allows doctors to modify experience, bio, and multi-select sub-specialties via an array of integers (IDs).",
        request=DoctorProfileSerialzer,
        responses={
            200: OpenApiResponse(
                response=DoctorProfileSerialzer,
                description="Profile updated successfully. Returns clean objects with text names."
            ),
            400: OpenApiResponse(
                description="Bad Request. Provided invalid format or non-existent specialization ID.",
                examples=[
                    OpenApiExample(
                        'Specialty ID Error Example',
                        value={"specialties": ["Invalid pk \"99\" - object does not exist."]},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(description="Unauthorized. Invalid or missing Bearer token.")
        }
    )
    def update(self, request, *args, **kwargs):
        res = super().update(request, *args, **kwargs)
        return Response({
            "data": res.data,
            "message": "Doctor profile updated successfully"}, status=200)
    

class DoctorEducationView(generics.CreateAPIView):
    serializer_class = DoctorEducationSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return Education.objects.filter(doctor=self.request.user.doctor)

    @extend_schema(
        summary="Add Education Certification",
        description="Allows a logged-in doctor to append an academic degree or certification to their history.",
        request=DoctorEducationSerializer,
        responses={201: OpenApiResponse(description="Doctor education added successfully.")}
    )
    def create(self, request, *args, **kwargs):
        # تصحيح الخطأ: تم تعديل البارامترات لتعمل بالتوافق مع بنية دجانغو الأساسية واستقبال الـ request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(doctor=request.user.doctor)
        return Response({"message": "Doctor education added successfully"}, status=201)

    def get_object(self):
        pk = self.kwargs.get('pk')
        return Education.objects.get(id=pk, doctor=self.request.user.doctor)


class ScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
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
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Doctor Available Slots by Date",
        description="Returns an array of available booking hours based on the doctor's weekly work schedule and specific date query parameter.",
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
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'doctor_username'

    def get_object(self):
        username_val = self.kwargs.get(self.lookup_field)
        doctor = get_object_or_404(Doctor, user__username=username_val)
        return doctor


class SubSpecializationListView(generics.ListAPIView):
    queryset = SubSpecialization.objects.all()
    serializer_class = SubSpecializationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List All Medical Specialties",
        description="Returns a complete array configuration containing all 11 psychological and medical specialties with their structural IDs.",
        responses={
            200: OpenApiResponse(
                response=SubSpecializationSerializer(many=True),
                description="List of all system specialties fetched successfully."
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DoctorListView(generics.ListAPIView):
    queryset = Doctor.objects.filter(status='approved')
    serializer_class = DoctorPublicProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['specialties']

    @extend_schema(
        summary="List Approved Doctors with Specialty Filtering",
        description="Fetches verified profiles. Patients can append the optional query parameter `?specialties=id` to display filtered options.",
        parameters=[
            OpenApiParameter(
                name="specialties",
                type=int,
                location=OpenApiParameter.QUERY,
                description="The exact database ID of the specialization to filter by (e.g., ?specialties=1)."
            )
        ],
        responses={
            200: OpenApiResponse(
                response=DoctorPublicProfileSerializer(many=True),
                description="Filtered list retrieved smoothly."
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)