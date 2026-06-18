from django.urls import path
from .views import RecommendedTracksView, LastFeelingView, BreathingExerciseListView

urlpatterns = [
    path('recommendations/', RecommendedTracksView.as_view(), name='patient-recommended-tracks'),
    path('feeling/last/', LastFeelingView.as_view(), name='patient-last-feeling'),
    path('breathing-exercises/', BreathingExerciseListView.as_view(), name='patient-breathing-exercises'),
]