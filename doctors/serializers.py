from rest_framework import serializers
from .models import (Doctor,
                     Job_title,
                     Education,
                     Schedule,
                     SubSpecialization)
from users.models import User, Otp
from users.serializers import UserDoctorSerializer
from appointments.serializers import PricesSerializer

from django.db import transaction 
from users.mail_sender import send_professional_email
from threading import Thread
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from appointments.models import Appointment

class DoctorRegisterSerializer(serializers.ModelSerializer):
    user = UserDoctorSerializer()
    class Meta:
        model = Doctor
        fields = ['user',]
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        
        with transaction.atomic():
            user_serializer = UserDoctorSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            doctor = Doctor.objects.create(user=user, **validated_data)
            code = Otp.generate_otp()
            hash_code = make_password(code)
            Otp.objects.create(user=user, code=hash_code)    
        Thread(target=send_professional_email, args=(user.email, code)).start()
        
        return doctor

class job_titleSerialzer(serializers.ModelSerializer):
    title = serializers.CharField(required=False)
    class Meta: 
        model = Job_title
        fields = ["title",] 

class UserUpdateSerialzer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = ["email" , "username" , 'gender','birth_date','phone','first_name',"last_name","age"]
        extra_kwargs = {'password': {'write_only': True}, "email": {"read_only": True}, "username": {"read_only": True}}

# تحديث السيريالايزر ليشمل الـ id والاسم معاً لتسهيل المعالجة في فلاتر
class SubSpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSpecialization
        fields = ["id", "name"]

class EducationsSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Education
        fields = ['degree','license_number','institution','graduation_year','status','created_at']
    
class DoctorProfileSerialzer(serializers.ModelSerializer):
    user = UserUpdateSerialzer(required=False)
    job_title = job_titleSerialzer(required=False)
    
    # التعديل الهندي الآمن: استقبال الـ IDs عند التحديث والـ PATCH
    specialties = serializers.PrimaryKeyRelatedField(
        queryset=SubSpecialization.objects.all(),
        many=True,
        required=False
    )
    session_prices = PricesSerializer(required=False, many=True)
    educations = EducationsSerializer(many=True, required=False)

    class Meta: 
        model = Doctor 
        fields = ['user', 'average_rating', 'patients_count', 'educations', 'photo', 'job_title', 'status', 'specialties', 'experience', "bio", 'session_prices']

    def update(self, instance, validated_data): 
        user_data = validated_data.pop('user', None)
        user = instance.user
        job_title_data = validated_data.pop('job_title', None)
        specialties_data = validated_data.pop('specialties', None)

        with transaction.atomic():
            instance.experience = validated_data.get('experience', instance.experience) 
            instance.bio = validated_data.get('bio', instance.bio)
            title = job_title_data.get('title') if job_title_data else None
            if title:
                job_title_obj, _ = Job_title.objects.get_or_create(title=title)
                instance.job_title = job_title_obj  
            
            instance.save()

            if user_data:
                user.gender = user_data.get('gender', user.gender)
                user.birth_date = user_data.get('birth_date', user.birth_date)
                user.phone = user_data.get('phone', user.phone)
                user.save()
            
            # تحديث التخصصات بشكل آمن تماماً بناءً على الـ IDs الممررة
            if specialties_data is not None:
                instance.specialties.set(specialties_data)

        return instance

    def to_representation(self, instance):
        # ميثود تضمن خروج البيانات مهيكلة بالاسم والـ ID عند طلب الـ GET لتطبيق الطبيب
        representation = super().to_representation(instance)
        representation['specialties'] = SubSpecializationSerializer(instance.specialties.all(), many=True).data
        return representation

class DoctorEducationSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Education
        fields = [
            'degree',
            'institution',
            'graduation_year',
            'license_number',
            'certificate'
        ]

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Schedule
        fields = ['id', 'day_of_week', 'start_time', 'end_time']
        
    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")
        
        return attrs

    def update(self, instance, validated_data):
        doctor = instance.doctor
        view = self.context.get('view')
        id = view.kwargs.get(view.lookup_field)

        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')
        day_of_week = validated_data.get("day_of_week")
        
        schedule = Schedule.objects.get(doctor=doctor, day_of_week=day_of_week, id=id)
        if not schedule: 
            raise serializers.ValidationError("Schedule not found for the specified day.")

        anotherSchedules = Schedule.objects.filter(~Q(id=schedule.id), doctor=doctor, day_of_week=day_of_week)
        for obj in anotherSchedules: 
            if start_time < obj.end_time and end_time > obj.start_time:
                raise serializers.ValidationError(f'This is Overlaps with {day_of_week} schedule')
            
        schedule.start_time = start_time
        schedule.end_time = end_time
        schedule.save()

        return validated_data

    def create(self, validated_data):
        doctor = self.context['request'].user.doctor
        day_of_week = validated_data.get('day_of_week')
        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')

        anotherSchedules = Schedule.objects.filter(doctor=doctor, day_of_week=day_of_week)
        for obj in anotherSchedules: 
            if start_time < obj.end_time and end_time > obj.start_time:
                raise serializers.ValidationError(f'This is Overlaps with {day_of_week} schedule')

        schedule = Schedule.objects.create(doctor=doctor, day_of_week=day_of_week, start_time=start_time, end_time=end_time)
        schedule.save()

        return validated_data

class AvailableSlotsSerializer(serializers.Serializer):
    date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    available_slots = serializers.SerializerMethodField()

    def get_available_slots(self, obj):
        doctor = obj['doctor']
        target_date = obj['date'] 
        day_name = target_date.strftime('%A')

        schedules = Schedule.objects.filter(doctor=doctor, day_of_week__iexact=day_name)

        if not schedules.exists():
            return []

        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            date__date=target_date,
            status__in=['pending', 'confirmed']
        ).order_by('date')
        
        booked_slots = []
        for app in existing_appointments:
            app_start = app.date.time()
            app_end = (app.date + timedelta(minutes=app.duration)).time()
            booked_slots.append((app_start, app_end))

        slot_duration = timedelta(minutes=30)
        slots_list = []

        for schedule in schedules:
            current_time = datetime.combine(target_date, schedule.start_time)
            end_datetime = datetime.combine(target_date, schedule.end_time)

            while current_time + slot_duration <= end_datetime:
                slot_start = current_time.time()
                slot_end = (current_time + slot_duration).time()

                is_booked = False
                for b_start, b_end in booked_slots:
                    if (b_start <= slot_start < b_end) or (b_start < slot_end <= b_end) or (slot_start <= b_start and slot_end >= b_end):
                        is_booked = True
                        break

                if not is_booked:
                    slots_list.append({
                        "start": slot_start.strftime('%H:%M'),
                        "end": slot_end.strftime('%H:%M')
                    })

                current_time += slot_duration

        return slots_list

class UserDoctorPublicProfileSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = User
        fields = ['username', 'first_name', 'last_name', 'age']

class DoctorPublicProfileSerializer(serializers.ModelSerializer):
    user = UserDoctorPublicProfileSerializer()
    job_title = job_titleSerialzer()
    specialties = SubSpecializationSerializer(many=True)
    session_prices = PricesSerializer(many=True)
    class Meta:
        model = Doctor
        fields = ['user', 'average_rating', 'patients_count', 'job_title', 'specialties', 'session_prices', 'bio', 'experience', 'photo']