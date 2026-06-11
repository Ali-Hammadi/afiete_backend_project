from django.urls import path
from .views import RatingCreateView, RatingListView

urlpatterns = [
    # تمرير معرف الموعد في الرابط لضمان تطبيق فحص الـ get_object_or_404 بأمان
    path('<int:appointment_id>/create/', RatingCreateView.as_view(), name='rating-create'), 
    path('<str:doctor_username>/', RatingListView.as_view(), name='rating-list'),
    path('', RatingListView.as_view(), name='rating-list'),
]