from django.urls import path
from .views import (
    DoctorAppointmentListView, DoctorWalletView, SessionPricesListCreateView, 
    SessionPricesRetrieveUpdateView, DoctorMissedSessionsListView, RetrieveAppointmentAPIView
)

urlpatterns = [
    path('dashboard/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),
    path('prices/', SessionPricesListCreateView.as_view(), name='doctor-prices-list'),
    path('prices/<str:type>/', SessionPricesRetrieveUpdateView.as_view(), name='doctor-prices-detail'),
    path('wallet/', DoctorWalletView.as_view(), name='doctor-wallet'),
    path('missed/', DoctorMissedSessionsListView.as_view(), name='doctor-missed-sessions'),
    path('<int:pk>/', RetrieveAppointmentAPIView.as_view(), name='doctor-appointment-detail'), # مشترك للقراءة
]