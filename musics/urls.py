
from django.urls import path
from .views import RecommendedTracksView, LastFeelingView, BreathingExerciseListView

urlpatterns = [

    path('recommendations/', RecommendedTracksView.as_view(), name='recommended-tracks'),
    
 
    path('feeling/last/', LastFeelingView.as_view(), name='last-feeling'),
    
    path('breathing-exercises/', BreathingExerciseListView.as_view(), name='breathing-exercises'),
]