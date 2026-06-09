import random
from datetime import datetime
from django.db.models import Q
from .models import MusicEntity, FeelingType, MusicTherapeuticGoal

def get_goal_for_feeling(feeling: str) -> str:
    mapping = {
        FeelingType.HAPPY: MusicTherapeuticGoal.UPLIFT,
        FeelingType.SAD: MusicTherapeuticGoal.CALM_DOWN,
        FeelingType.ANGRY: MusicTherapeuticGoal.CALM_DOWN,
        FeelingType.NEUTRAL: MusicTherapeuticGoal.STABILIZE,
        FeelingType.ANXIOUS: MusicTherapeuticGoal.CALM_DOWN,
    }
    return mapping.get(feeling, MusicTherapeuticGoal.STABILIZE)

def get_recommended_tracks(feeling: str, limit: int = 5, exclude_track_id: str = None):
    # 1. Try matching by target feeling
    queryset = MusicEntity.objects.filter(supported_feelings__contains=feeling)
    
    if exclude_track_id:
        queryset = queryset.exclude(id=exclude_track_id)
        
    pool = list(queryset)
    
    # 2. Fallback to therapeutic goal matching if feeling pool is empty
    if not pool:
        fallback_goal = get_goal_for_feeling(feeling)
        fallback_queryset = MusicEntity.objects.filter(therapeutic_goals__contains=fallback_goal)
        if exclude_track_id:
            fallback_queryset = fallback_queryset.exclude(id=exclude_track_id)
        pool = list(fallback_queryset)
        
    if not pool:
        return []

    # 3. Apply Novelty Sorting & Shifting Seed Rotation matching Flutter logic
    # Sort descending by novelty_score
    pool.sort(key=lambda x: x.novelty_score, reverse=True)
    
    if len(pool) > 1:
        # Recreate Flutter's daily deterministic shift per feeling type
        try:
            feeling_index = list(FeelingType).index(feeling)
        except ValueError:
            feeling_index = 0
            
        seed_value = datetime.now().day + (feeling_index * 17)
        
        # Shuffle deterministically using a local Random instance instance
        rng = random.Random(seed_value)
        rng.shuffle(pool)
        
    return pool[:limit]