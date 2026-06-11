from django.urls import path
from .views import RefundAppointmentView
from .views import (
    BookAppointmentView, 
    PatientAppointmentListView, 
    PatientPastAppointmentsListView,
    DoctorAppointmentListView,
    CancelAppointmentView, 
    RetrieveAppointmentAPIView, 
    RescheduleAppointmentView,
    CreatePaymentView, 
    PaymentListView,
    DoctorWalletView,  
    SessionPricesListCreateView,       
    SessionPricesRetrieveUpdateView,
    PatientMissedSessionsListView,
    DoctorMissedSessionsListView,
    PatientUpdateNextSessionView
)

urlpatterns = [
    # ==================== 🩺 Doctor Views ====================
    path('dashboard/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),
    path('prices/', SessionPricesListCreateView.as_view(), name='doctor-prices-list'),
    path('prices/<str:type>/', SessionPricesRetrieveUpdateView.as_view(), name='doctor-prices-detail'),
    path('doctor/wallet/', DoctorWalletView.as_view(), name='doctor-wallet'),
    path('doctor/missed/', DoctorMissedSessionsListView.as_view(), name='doctor-missed-sessions'),

    # ==================== 👥 Patient Views ====================
    path('book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('my-list/', PatientAppointmentListView.as_view(), name='patient-appointments'),
    path('history/', PatientPastAppointmentsListView.as_view(), name='patient-appointments-history'),   
    path('patient/missed/', PatientMissedSessionsListView.as_view(), name='patient-missed-sessions'),
    path('payments/create/', CreatePaymentView.as_view(), name='payment-create'),
    path('<int:appointment_id>/refund/', RefundAppointmentView.as_view(), name='refund-appointment'),

    # ==================== 🔒 Shared / Specific Actions ====================
    path('<int:pk>/', RetrieveAppointmentAPIView.as_view(), name='appointment-detail'),
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('<int:pk>/reschedule/', RescheduleAppointmentView.as_view(), name='reschedule-appointment'),
    path('<int:pk>/next-session/', PatientUpdateNextSessionView.as_view(), name='patient-update-next-session'),
    path('payments/history/', PaymentListView.as_view(), name='payment-list'),
    
]