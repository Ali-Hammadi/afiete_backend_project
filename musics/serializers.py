from rest_framework import serializers
from .models import MusicEntity, BreathingExerciseEntity, UserRelaxProfile

class MusicEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MusicEntity
        fields = '__all__'

class BreathingExerciseEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BreathingExerciseEntity
        fields = '__all__'