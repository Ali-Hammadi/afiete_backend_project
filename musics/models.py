from django.db import models
from django.contrib.auth import get_user_model
import random

User = get_user_model()

class FeelingType(models.TextChoices):
    HAPPY = 'happy', 'Happy'
    SAD = 'sad', 'Sad'
    ANGRY = 'angry', 'Angry'
    NEUTRAL = 'neutral', 'Neutral'
    ANXIOUS = 'anxious', 'Anxious'

class MusicTherapeuticGoal(models.TextChoices):
    CALM_DOWN = 'calmDown', 'Calm Down'
    UPLIFT = 'uplift', 'Uplift'
    STABILIZE = 'stabilize', 'Stabilize'
    FOCUS = 'focus', 'Focus'
    SLEEP = 'sleep', 'Sleep'

class MusicSourceType(models.TextChoices):
    BENSOUND = 'bensound', 'Bensound'
    FREEMUSICARCHIVE = 'freemusicarchive', 'Free Music Archive'
    PIXABAY = 'pixabay', 'Pixabay'
    INCOMPETECH = 'incompetech', 'Incompetech'
    CUSTOM = 'custom', 'Custom'

class BreathingExerciseType(models.TextChoices):
    BOX_BREATHING = 'boxBreathing', 'Box Breathing'
    FOUR_SEVEN_EIGHT = 'fourSevenEight', '4-7-8 Breathing'
    DIAPHRAGMATIC = 'diaphragmatic', 'Diaphragmatic Breathing'
    PACED_BREATHING = 'pacedBreathing', 'Paced Breathing'
    RESONANCE = 'resonance', 'Resonance Breathing'


class MusicEntity(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    audio_url = models.URLField()
    preview_url = models.URLField(blank=True, null=True)
    cover_url = models.URLField(blank=True, null=True)
    source_name = models.CharField(max_length=100)
    source_url = models.URLField()
    source_type = models.CharField(max_length=50, choices=MusicSourceType.choices, default=MusicSourceType.CUSTOM)
    
    # Storing lists as JSON for clean architecture mapping
    supported_feelings = models.JSONField(help_text="List of FeelingType strings")
    therapeutic_goals = models.JSONField(help_text="List of MusicTherapeuticGoal strings")
    
    is_instrumental = models.BooleanField(default=True)
    duration_seconds = models.IntegerField()
    tempo_bpm = models.IntegerField()
    novelty_score = models.IntegerField(default=5)
    license_text = models.TextField()
    attribution_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.artist}"


class BreathingExerciseEntity(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=BreathingExerciseType.choices)
    duration_minutes = models.IntegerField()
    inhale_seconds = models.IntegerField()
    hold_seconds = models.IntegerField()
    exhale_seconds = models.IntegerField()
    rest_seconds = models.IntegerField()
    steps = models.JSONField(help_text="Ordered list of string steps")
    recommended_for = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class UserRelaxProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='relax_profile')
    last_selected_feeling = models.CharField(max_length=20, choices=FeelingType.choices, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Relax Profile for {self.user.username}"