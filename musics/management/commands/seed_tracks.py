from django.core.management.base import BaseCommand
from musics.models import MusicEntity, BreathingExerciseEntity

class Command(BaseCommand):
    help = 'Seeds initial therapeutic tracks and breathing exercises'

    def handle(self, *args, **kwargs):
        # Seed Music
        tracks = [
            {
                "id": "music_01", "title": "Cozy Coffeehouse", "artist": "Lunar Years",
                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                "supported_feelings": ["neutral", "anxious", "sad"],
                "therapeutic_goals": ["calmDown", "stabilize", "sleep"],
                "duration_seconds": 180, "tempo_bpm": 72, "novelty_score": 8
            },
            {
                "id": "music_02", "title": "Small Joys", "artist": "Aventure",
                "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                "supported_feelings": ["happy", "neutral"],
                "therapeutic_goals": ["uplift", "stabilize"],
                "duration_seconds": 165, "tempo_bpm": 88, "novelty_score": 9
            }
        ]
        
        for t in tracks:
            MusicEntity.objects.update_or_create(
                id=t["id"],
                defaults={
                    "title": t["title"], "artist": t["artist"], "audio_url": t["audio_url"],
                    "supported_feelings": t["supported_feelings"], "therapeutic_goals": t["therapeutic_goals"],
                    "duration_seconds": t["duration_seconds"], "tempo_bpm": t["tempo_bpm"],
                    "novelty_score": t["novelty_score"], "source_name": "SoundHelix",
                    "source_url": "https://www.soundhelix.com/audio-examples", "is_instrumental": True
                }
            )

        # Seed Exercises
        exercises = [
            {
                "id": "breath_01", "title": "Box Breathing", "type": "boxBreathing", "duration_minutes": 5,
                "inhale_seconds": 4, "hold_seconds": 4, "exhale_seconds": 4, "rest_seconds": 4,
                "steps": ["Inhale for 4 seconds", "Hold for 4 seconds", "Exhale for 4 seconds", "Hold for 4 seconds"],
                "recommended_for": "Stress, focus, and emotional reset"
            }
        ]
        
        for e in exercises:
            BreathingExerciseEntity.objects.update_or_create(
                id=e["id"],
                defaults=e
            )
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded database.'))