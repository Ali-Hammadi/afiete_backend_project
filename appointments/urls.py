from rest_framework.routers import DefaultRouter
from .views import (BookAppointmentView,
                    PatientAppointmentListView,
                    DoctorAppointmentListView,
                    CancelAppointmentView,
                    RetrieveAppointmentAPIView,
                    RescheduleAppointmentView,
                    CreatePaymentView,
                    PaymentListView)
from django.urls import path
urlpatterns = [
    path('', BookAppointmentView.as_view(), name='book-appointment'),
    path('my-appointments/', PatientAppointmentListView.as_view(), name='patient-appointments'),
    path('doctor-dashboard/', DoctorAppointmentListView.as_view(), name='doctor-appointments'),

    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('<int:pk>/reschedule/', RescheduleAppointmentView.as_view()),
    path('<int:pk>', RetrieveAppointmentAPIView.as_view(), name='retrieve'),

    # paymetns
    path('payments/create', CreatePaymentView.as_view()),
    path('payments/', PaymentListView.as_view()),
]