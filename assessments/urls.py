from django.urls import path
# التعديل هنا: قمنا باستيراد RecommendedTracksView من musics.views
from .views import (
    ServeyFormView, SubmitAnswerView, PatientScoresView, RecommendDoctorsView
)
from musics.views import RecommendedTracksView, LastFeelingView, BreathingExerciseListView

urlpatterns = [
    path('form/', ServeyFormView.as_view(), name='servey-form'),
    path('form/submit/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('scores/', PatientScoresView.as_view(), name='patient-scores'),
    path('doctors/recommend/', RecommendDoctorsView.as_view(), name='recommend-doctors'),
    
    # الروابط الخاصة بالـ Musics التي تم جلبها من تطبيق musics
    path('recommendations/', RecommendedTracksView.as_view(), name='recommended-tracks'),
    path('feeling/last/', LastFeelingView.as_view(), name='last-feeling'),
    path('breathing-exercises/', BreathingExerciseListView.as_view(), name='breathing-exercises'),
]