from django.urls import path
from .views import ServeyFormView , SubmitAnswerView, PatientScoresView, RecommendDoctorsView

urlpatterns = [
    path('form/', ServeyFormView.as_view(), name='servey-form'),
    path('form/submit/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('scores/', PatientScoresView.as_view()),
    path('doctors/recommend/', RecommendDoctorsView.as_view()),

# urls.py

]# urls.py