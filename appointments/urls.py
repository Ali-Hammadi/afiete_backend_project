from django.urls import path
from .views import (
    BookAppointmentView, PatientAppointmentListView, DoctorAppointmentListView,
    CancelAppointmentView, RetrieveAppointmentAPIView, RescheduleAppointmentView,
    CreatePaymentView, PaymentListView
)

urlpatterns = [
    # --- منظور المريض (api/patient/appointments/) ---
    path('book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('my-list/', PatientAppointmentListView.as_view(), name='patient-appointments'),
    
    # المدفوعات التابعة للمريض
    path('payments/create/', CreatePaymentView.as_view(), name='payment-create'),
    path('payments/history/', PaymentListView.as_view(), name='payment-list'),

    # --- منظور الطبيب (api/doctor/appointments/) ---
    path('dashboard/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),

    # --- مشتركة حسب المعرّف (ID) والصلاحية تتحكم بالوصول ---
    path('<int:pk>/', RetrieveAppointmentAPIView.as_view(), name='appointment-detail'),
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('<int:pk>/reschedule/', RescheduleAppointmentView.as_view(), name='reschedule-appointment'),
]