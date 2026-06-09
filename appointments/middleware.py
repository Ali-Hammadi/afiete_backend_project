# middleware.py
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
import re
class CancelExpiredAppointmentsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/appointments') or \
           request.path.startswith('/api/doctors/{doctor_username}/available-slots/') or \
           re.match(r'^/api/doctors/\w+/available-slots/', request.path) or \
            re.match(r'^/api/appointments/\d+/reschedule/', request.path):
            self._cancel_expired()
        response = self.get_response(request)
        return response

    def _cancel_expired(self):
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)

        # الحجوزات التي مضى عليها ساعة بدون دفع
        Appointment.objects.filter(
            status='pending',
            created_at__lte=one_hour_ago
        ).exclude(payment__isnull=False).update(status='expired')

        #  الحجوزات المؤكدة التي انتهى وقت موعدها
        for appointment in Appointment.objects.filter(status='confirmed'):
            end_time = appointment.date + timedelta(minutes=appointment.duration)
            if end_time <= now:
                appointment.status = 'completed'
                appointment.save()