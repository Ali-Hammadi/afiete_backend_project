from django.urls import path

from .views import *
urlpatterns = [
   path('register/', PatientRegisterView.as_view(), name='patient-register'),
   path('profile/', PatientProfileView.as_view(), name='patient-profile'),
   path('google/auth/', GoogleAuthView.as_view(), name='google-auth'),
]