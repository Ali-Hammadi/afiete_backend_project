from .models import *
from rest_framework.response import Response
from rest_framework import generics
from .serializers import PatientRegisterSerializer , PatientProfileSerializer , GoogleAuthSerializer
from rest_framework import permissions
from users.permissions import IsAccountActiveAndUnfrozen, IsPatient, IsDoctor
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.conf import settings
from django.db import transaction
from rest_framework import status
from users.permissions import IsAccountActiveAndUnfrozen
import uuid 

class PatientRegisterView(generics.CreateAPIView):
    serializer_class = PatientRegisterSerializer
    
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({"message": "Patient registered successfully"
                          , "is_verified":False},
                           status=201)

class PatientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PatientProfileSerializer
    queryset = Patient.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    def get_object(self):
        return self.request.user.patient


class GoogleAuthView(APIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = []
    def post(self, request, *args, **kwargs):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['id_token']
        
        idinfo = id_token.verify_oauth2_token(token, 
                                                requests.Request(),
                                                settings.GOOGLE_CLIENT_ID)
        email = idinfo.get('email')
        if not email:
            return Response({"error": "Email not found in token"}, status=status.HTTP_400_BAD_REQUEST)
        
        first_name = idinfo.get('given_name', 'user')
        last_name = idinfo.get('family_name', '')
        username = f"{first_name}_{last_name}_{str(uuid.uuid4())[:8]}".lower()
        with transaction.atomic():
            user, created = User.objects.get_or_create(email=email,username=username, defaults={'first_name': first_name, 'last_name': last_name})
            patient , _ = Patient.objects.get_or_create(user=user)
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Authentication successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "role": "patient"
            }, status=status.HTTP_200_OK)
            

class DoctorRetrievePatientView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]
    
    def get_object(self):
        patient = super().get_object()
        
        doctor = self.request.user.doctor
        
        appointment_exists = Appointment.objects.filter(doctor=doctor, patient=patient).exists()
        
        if not appointment_exists:
            raise PermissionDenied("Access denied: No appointment found between this doctor and patient.")
            
        return patient