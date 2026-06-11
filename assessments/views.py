from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework import generics
from rest_framework.views import APIView
from assessments.models import QuestionGroup , UserAnswer
from .serializers import ServeyFormSerializer, UserAnswerSerializer , SubmitAnswerSerializer, ScoresSerializer
from .recommender import recommend_doctors
from .pagination import DoctorPagination
from users.permissions import IsDoctor, IsPatient
from rest_framework.permissions import IsAuthenticated
from appointments.models import Appointment
from doctors.models import Schedule
from django.shortcuts import get_object_or_404
from rest_framework import status
from appointments.serializers import AppointmentSerializer
from users.permissions import IsAccountActiveAndUnfrozen
from musics.views import RecommendedTracksView
from drf_spectacular.utils import extend_schema
class ServeyFormView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServeyFormSerializer
    queryset = QuestionGroup.objects.prefetch_related('questions__options').all()  

class SubmitAnswerView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    serializer_class = SubmitAnswerSerializer 
    queryset = UserAnswer.objects.all() 
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Answer saved successfully."},
            status=200
        )

# questionnaire/views.py

class PatientScoresView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        scores = ScoresSerializer(request.user.patient).data
        return Response(scores)

# doctors/views.py

class RecommendDoctorsView(APIView):
    permission_classes = [IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    def get(self, request):
        patient     = request.user.patient
        recommended = recommend_doctors(patient)

        # حجم الصفحة افتراضي 5
        paginator = DoctorPagination()
        paginator.page_size = 1
        page = paginator.paginate_queryset(recommended, request)
        
        return paginator.get_paginated_response(page)


    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)
        
        new_date = request.data.get('new_date')
        new_time_slot_id = request.data.get('new_time_slot_id')
        new_appointment_type = request.data.get('appointment_type') # إعادة تعيين نوع الحجز

        # 2. التحقق من توفر الموعد الجديد
        new_slot = get_object_or_404(Schedule, id=new_time_slot_id, doctor=appointment.doctor, date=new_date)
        if new_slot.is_booked:
            return Response({"error": "The new appoinmemt is booked already."}, status=status.HTTP_400_BAD_REQUEST)

        if appointment.time_slot:
            old_slot = appointment.time_slot
            old_slot.is_booked = False
            old_slot.save()

        new_slot.is_booked = True
        new_slot.save()

        appointment.date = new_date
        appointment.time_slot = new_slot
        appointment.appointment_type = new_appointment_type
        appointment.status = 'scheduled' 
        appointment.save()

        serializer = AppointmentSerializer(appointment)
        return Response({
            "message": "The new reschedual is corect now .",
            "appointment": serializer.data
        }, status=status.HTTP_200_OK)