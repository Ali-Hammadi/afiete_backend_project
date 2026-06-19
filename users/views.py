from tokenize import TokenError
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response
from rest_framework import generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from .serializers import EmptySerializer
from doctors.views import EmptySerializer
from .models import User, Otp
from .permissions import IsAccountActiveAndUnfrozen
from .serializers import ( UserLoginSerializer,
                           ResendOtpSerializer,
                           VerifyOtpSerializer,
                           PasswordResetSerializer,
                           EmailResetSerializer,
                           UserInfoSerializer,
                           ForgetPasswordVerifyOtpSerializer,
                           ForgetPasswordSerializer,
                           ResetPasswordSerializer,
                           DeactivateUserSerializer,
                           ActivateUserSerializer
                           )
from .mail_sender import send_professional_email
from .utils import *
from drf_spectacular.utils import extend_schema, inline_serializer
from doctors.serializers import DoctorProfileSerialzer
from patients.serializers import PatientProfileSerializer

from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404

import threading


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    def post(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = User.objects.filter(email = serializer.data.get('email')).first()
        user_data = UserInfoSerializer(user).data
    

        refresh = RefreshToken.for_user(user)
        
        role = "doctor" if is_doctor(user) else "patient" if is_patient(user) else "Anonymous"
        details = ""
        if role == "doctor":
            details = DoctorProfileSerialzer(user.doctor).data
        elif role == "patient":
            details = PatientProfileSerializer(user.patient).data
        return Response({"message": "Login successful",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "role": str(role),
                "user":user_data,
                str(role): details
                }, status=200)

class ResendOtpView(generics.GenericAPIView):
    serializer_class = ResendOtpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=200)

class VerifyOtpView(generics.GenericAPIView):
    serializer_class = VerifyOtpSerializer
    
    def post(self, request, *args, **kwargs):
        get_object_or_404(User, email=request.data.get('email'))
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if not user: 
            return Response(
                {"message": "invalid otp"},
                400
            )
        refresh = RefreshToken.for_user(user)

        return Response(
             {      "is_verified":user.is_verified,
                    "is_active": user.is_active,
                    "message": "OTP verified successfully",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token) 
             },
             status=200)
class LogoutView(APIView):
    """
    تسجيل الخروج وإبطال عمل الـ Refresh Token بوضعه في القائمة السوداء.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer  # لتوثيق الواجهة بشكل سليم

    @extend_schema(
        summary="User Logout / Blacklist Token",
        description="Invalidate the refresh token upon user logout.",
        request=inline_serializer(
            name='LogoutRequest',
            fields={
                'refresh_token': drf_serializers.CharField(required=True, help_text="The refresh token to be blacklisted.")
            }
        ),
        responses={
            200: inline_serializer(
                name='LogoutResponse',
                fields={'message': drf_serializers.CharField()}
            ),
            400: drf_serializers.DictField()
        }
    )
    def post(self, request, *args, **kwargs):
        # استخراج الـ refresh_token من جسم الطلب
        refresh_token = request.data.get("refresh_token")
        
        if not refresh_token:
            return Response(
                {"error": "refresh_token field is required in request body."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # محاولة جلب التوكن وإضافته للقائمة السوداء
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logged out successfully. Token has been blacklisted."}, 
                status=status.HTTP_200_OK
            )
            
        except TokenError as e:
            return Response(
                {"error": "Invalid or expired refresh token."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # في حال لم تكن حزمة البلاكليست مفعلة في الإعدادات أو حدث خطأ آخر
            return Response(
                {"error": "Blacklisting feature is not enabled or an error occurred."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
class PasswordResetView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = PasswordResetSerializer

    def get_object(self):
        return self.request.user
    def update(self,request):
        serializer = self.get_serializer(self.get_object(),data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message":"Password reseted successfully",
        },status=status.HTTP_200_OK)

class EmailResetView(generics.UpdateAPIView):
    queryset = User.objects.all()   
    permission_classes = [IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = EmailResetSerializer
    def update(self,request):
        serializer = self.get_serializer(self.get_object(),data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message":"Email reseted successfully, please verify your new email",
         },status=status.HTTP_200_OK) 
        
    def get_object(self):
        return self.request.user

class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ForgetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data = self.request.data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {"message": "OTP sent to your email"},
            status=status.HTTP_200_OK
        )


class ForgetPasswordVerifyOtpView(generics.GenericAPIView):
    serializer_class = ForgetPasswordVerifyOtpSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "OTP verified successfully"
             , "can_reset_password":True
             , "is_verified":True
             },
            status=status.HTTP_200_OK
        )


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password reset successfully"},
            status=status.HTTP_200_OK
        )

class DeactivateAccountView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAccountActiveAndUnfrozen]
    serializer_class = DeactivateUserSerializer
    def delete(self, request):
        # validation 
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.is_active = False
        user.save()

        # Band all tokens belong to user 
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        return Response(
            {"message": "Account deactivated successfully"},
            status=status.HTTP_200_OK
        )

class ActivateUserView(generics.GenericAPIView): 
    permission_classes = [AllowAny]
    serializer_class = ActivateUserSerializer

    def post(self, request): 
        serializer = self.get_serializer(data=request.data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "OTP sent to your email"
            }
        )
