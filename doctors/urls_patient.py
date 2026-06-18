from django.urls import path
from .views import DoctorListView, SubSpecializationListView, AvailableSlotsView, DoctorPublicProfileView

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('specialties/', SubSpecializationListView.as_view(), name='specialties-list'),
    path('<str:doctor_username>/available_slots/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('<str:doctor_username>/profile/public/', DoctorPublicProfileView.as_view(), name='doctor-profile-public'),
]