from django.urls import path
from .views import RatingCreateView, RatingListView
urlpatterns = [
    path('create/', RatingCreateView.as_view(), name='rating-create'), 
    path('<str:doctor_username>/', RatingListView.as_view(), name='rating-list'),
    path('', RatingListView.as_view(), name='rating-list'),
]