from rest_framework import serializers 
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class RatingReadSerializer(serializers.ModelSerializer):
    patient_nickname = serializers.CharField(source='appointment.patient.nickname', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'patient_nickname', 'rating', 'comment', 'created_at']