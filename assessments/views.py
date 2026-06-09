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


class ServeyFormView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServeyFormSerializer
    queryset = QuestionGroup.objects.prefetch_related('questions__options').all()  

class SubmitAnswerView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsPatient]
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
    permission_classes = [IsAuthenticated, IsPatient]
    def get(self, request):
        patient     = request.user.patient
        recommended = recommend_doctors(patient)

        # حجم الصفحة افتراضي 5
        paginator = DoctorPagination()
        paginator.page_size = 1
        page = paginator.paginate_queryset(recommended, request)
        
        return paginator.get_paginated_response(page)