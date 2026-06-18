from rest_framework import serializers
from users.models import User
from users.models import Otp
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import is_doctor , is_patient
from .mail_sender import send_email
from django.utils import timezone
from django.contrib.auth.hashers import make_password , check_password
from django.db import transaction
import uuid
import threading


class EmptySerializer(serializers.Serializer):
    pass

class UserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=100)
    email = serializers.EmailField(validators=[])
    class Meta:
        model = User
        fields = ['nickname','email','password']
        extra_kwargs = {'password': {'write_only': True}}
     
    
    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if user: 
            raise serializers.ValidationError({"message":"A user with this email already exists.",
                                               "is_active":user.is_active})
        return value
    def create(self, validated_data):
            nickname = (validated_data.get('nickname') or 'patient').strip()

            username = f"{nickname}_{str(uuid.uuid4())[:8]}".lower()
            user = User.objects.create_user(
                username=username,
                email=validated_data.get('email'),
                password=validated_data.get('password'),
            )

            return user 
    
class UserDoctorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])

    class Meta:
        model = User
        fields = ['email','password','first_name','last_name']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        user = User.objects.filter(email=value).first()
        if user: 
            raise serializers.ValidationError({"message":"A user with this email already exists.",
                                               "is_active":user.is_active})
        return value
    def create(self, validated_data):
        first_name = (validated_data.get('first_name') or '').strip()
        last_name = (validated_data.get('last_name') or '').strip()
    
        username = f"{first_name or 'user'}_{last_name or 'doc'}_{str(uuid.uuid4())[:8]}".lower()
        user = User.objects.create_user(
            username=username,
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            first_name=first_name,
            last_name=last_name
        )
    
        return user 

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'age']
class UserLoginSerializer(serializers.Serializer):  
    email = serializers.EmailField()
    password = serializers.CharField() 

    def validate(self, attrs):
        users = User.objects.filter(email=attrs['email'])
        if not users:
            raise serializers.ValidationError("User with this email does not exist.")
        user = users.first()    
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError("Incorrect password.")
        if not user.is_active: 
            raise serializers.ValidationError({"message":"This account has been deactivated.",
                                              "is_active": False})
        if not user.is_verified:
            raise serializers.ValidationError({
                      "message":"Account is not verified. Please verify your account before logging in.",
                      "is_verified": False,
                      })
        attrs['user'] = user
        return attrs

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']

        # إنشاء OTP جديد
        user = User.objects.filter(email=email).first()

        if not user:
            raise serializers.ValidationError(
                {"email": "User with this email does not exist"}
            )

        if user.is_verified:
            raise serializers.ValidationError(
                {"email": "User is already verified"}
            )
        Otp.objects.filter(user=user, is_used=False).update(is_used=True)
        code = Otp.generate_otp()
        hashed_code = make_password(code)
        new_otp = Otp.objects.create(
            user=user,
            code= hashed_code
        )

        threading.Thread(target=send_email, args=(user.email, code)).start()

        return {"message": "New OTP generated and sent successfully"}
    


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    def create(self, validated_data):
        email = validated_data['email']
        code = validated_data['code']

        otps = Otp.objects.filter(
            user__email=email,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

        for otp in otps:
            if check_password(code, otp.code):
                otp.is_used = True
                otp.save()

                user = otp.user
                user.is_verified = True
                if not user.is_active: 
                    user.is_active = True
                user.save()
 
                

                return user

        return False

class PasswordResetSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['password', "new_password" , "confirm_password"]
    def validate_password(self,value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password")
        if self.initial_data['new_password'] != self.initial_data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match")
        return value
    
    def update(self,instance,validated_data):
        user = instance
        new_password = validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
class EmailResetSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField(write_only=True)
    new_email = serializers.EmailField(write_only=True)
    class Meta:
        model = User
        fields = ['new_email','password','refresh']
        extra_kwargs = {'password': {'write_only': True}}
    def validate_password(self,value):
        user = self.context['request'].user 
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password")
        return value
    def update(self,instance,validated_data):
        user = instance
        email = validated_data['new_email']
        refresh = validated_data['refresh']
        token = RefreshToken(refresh)

        with transaction.atomic():

            # log out user from all devices by blacklisting the refresh token
            token.blacklist()
            
            # update email and set is_verified to false
            user.email = email
            user.is_verified = False # بعد تغيير الايميل يجب اعادة التحقق منه
            user.can_reset_password = False
            user.save()

            # send otp
            code = Otp.generate_otp()
            hashed_code = make_password(code)
            new_otp = Otp.objects.create(
                user=user,
                code= hashed_code
            )
        threading.Thread(target=send_email, args=(user.email, code)).start()
        return user

class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()
    
    def validate(self, attrs):
        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError('invalid request')
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = validated_data['user']

        code = Otp.generate_otp()
        hashed_code = make_password(code)
        Otp.objects.create(user=user, code=hashed_code)

        threading.Thread(target=send_email, args=(user.email, code)).start()

        return validated_data   


class ForgetPasswordVerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
   

    def create(self, validated_data):
        email = validated_data['email']
        code = validated_data['code']
       

        otps = Otp.objects.filter(
            user__email=email,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')

        for otp in otps:
            if check_password(code, otp.code):
                otp.is_used = True
                otp.save()

                user = otp.user
                user.can_reset_password = True

                user.save()
                return validated_data

        raise serializers.ValidationError({"detail": "Invalid OTP or email"})


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")

        user = User.objects.filter(email=attrs['email']).first()
        if not user:
            raise serializers.ValidationError("Invalid request")
        
        if not user.can_reset_password:
            raise serializers.ValidationError("Please verify OTP first")

        return attrs

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.can_reset_password = False
        user.save()
        return user

class DeactivateUserSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self,value): 
        user = self.context['request'].user
        if not user.check_password(value): 
            raise serializers.ValidationError("Incorrect Password")
        return value


class ActivateUserSerializer(serializers.Serializer):  
    email = serializers.EmailField()
    password = serializers.CharField() 

    def validate(self, attrs):
        users = User.objects.filter(email=attrs['email'])
        if not users:
            raise serializers.ValidationError("User with this email does not exist.")
        user = users.first()    
        if not user.check_password(attrs['password']):
            raise serializers.ValidationError("Incorrect password.")
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = User.objects.filter(email=validated_data['email']).first()
        print(user.email)
        Otp.objects.filter(user=user, is_used=False).update(is_used=True)
        code = Otp.generate_otp()
        hashed_code = make_password(code)
        Otp.objects.create(
            user=user,
            code= hashed_code
        )

        threading.Thread(target=send_email, args=(user.email, code)).start()
        return validated_data