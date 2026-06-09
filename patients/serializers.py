from rest_framework import serializers
from django.db import transaction
from .models import Patient
from random import randint
from users.models import User
from users.models import Otp
from users.mail_sender import send_email
from users.serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from users.serializers import UserSerializer
from threading import Thread
class OtpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Otp
        fields = ['user', 'code', 'is_used', 'created_at']
    
class PatientRegisterSerializer(serializers.ModelSerializer):
        user = UserSerializer()
        class Meta:
            model = Patient
            fields = ['user']
        def create(self, validated_data):
            otp_code = Otp.generate_otp()
            hashed_otp_code = make_password(otp_code)
            with transaction.atomic():
                userserializer = UserSerializer(data=validated_data['user'])
                userserializer.is_valid(raise_exception=True)
                user = userserializer.save()
                patient = Patient.objects.create(user=user,nickname=validated_data['user'].get('nickname', ''))
                Otp.objects.create(user=user, code=hashed_otp_code)
            Thread(target=send_email, args=(user.email, otp_code)).start()
            return patient
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email','username','birth_date','gender', 'phone', 'age']
        extra_kwargs = {'email': {'read_only': True},
                        'username': {'read_only': True}}
        
class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserUpdateSerializer()
    class Meta:
        model = Patient
        fields = ['user','psychological_history','nickname']
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        user = instance.user
        user.birth_date = user_data.get('birth_date', instance.user.birth_date)
        user.gender = user_data.get('gender', instance.user.gender)
        user.phone = user_data.get('phone', instance.user.phone)    
        user.save()

        instance.psychological_history = validated_data.get('psychological_history', instance.psychological_history)
        instance.save()

        return instance

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField() 
    def validate(self, attrs):
        id_token = attrs.get("id_token","")
        if not id_token:
            raise serializers.ValidationError("ID token is required")

        return attrs