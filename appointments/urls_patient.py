from django.urls import path
from .views import (
    BookAppointmentView, PatientAppointmentListView, PatientPastAppointmentsListView,
    PatientMissedSessionsListView, CreatePaymentView, RefundAppointmentView,
    CancelAppointmentView, RescheduleAppointmentView, PatientUpdateNextSessionView,
    PaymentListView, RetrieveAppointmentAPIView
)

urlpatterns = [
    path('book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('my-list/', PatientAppointmentListView.as_view(), name='patient-appointments'),
    path('history/', PatientPastAppointmentsListView.as_view(), name='patient-appointments-history'),   
    path('missed/', PatientMissedSessionsListView.as_view(), name='patient-missed-sessions'),
    path('payments/create/', CreatePaymentView.as_view(), name='payment-create'),
    path('payments/history/', PaymentListView.as_view(), name='payment-list'),
    path('<int:appointment_id>/refund/', RefundAppointmentView.as_view(), name='refund-appointment'),
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('<int:pk>/reschedule/', RescheduleAppointmentView.as_view(), name='reschedule-appointment'),
    path('<int:pk>/next-session/', PatientUpdateNextSessionView.as_view(), name='patient-update-next-session'),
    path('<int:pk>/', RetrieveAppointmentAPIView.as_view(), name='patient-appointment-detail'), # مشترك للقراءة
]