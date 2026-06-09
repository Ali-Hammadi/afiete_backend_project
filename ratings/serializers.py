from rest_framework import serializers 
from .models import Rating
from django.utils import timezone
class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_appointment(self, value):
        if value is None:
            raise serializers.ValidationError("Appointment must be provided.")
        
        # التاكد من أن المريض الذي يقوم بالتقييم هو نفس المريض الذي حضر الموعد
        appointment = value
        patient = self.context['request'].user.patient
        if appointment.patient != patient:
            raise serializers.ValidationError("Appointment does not exist.")
        return value 
    # التاكد من أن الوقت الحالي بعد موعد الحجز
    def validate(self, data):
        appointment = data.get('appointment')
        
        if appointment and appointment.date > timezone.now():
            raise serializers.ValidationError("Cannot rate an appointment that has not occurred yet.")
        return data


class RatingReadSerializer(serializers.ModelSerializer):
    patient_nickname = serializers.CharField(source='appointment.patient.nickname', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'patient_nickname', 'rating', 'comment', 'created_at'] 