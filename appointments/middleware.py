from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from django.db.models import F
import re

class CancelExpiredAppointmentsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # تنفيذ الفحص فقط عند الحاجة لتخفيف الضغط
        if any(path in request.path for path in ['/api/appointments', '/api/doctors/', '/api/doctors/']):
            self._cancel_expired()
        return self.get_response(request)

    def _cancel_expired(self):
        now = timezone.now()
        
        # 1. إلغاء الحجوزات المعلقة التي مر عليها أكثر من ساعة (استعلام جماعي)
        one_hour_ago = now - timedelta(hours=1)
        Appointment.objects.filter(
            status='pending',
            created_at__lte=one_hour_ago
        ).update(status='expired')

        # 2. إنهاء الحجوزات المؤكدة التي انتهى وقتها (استعلام جماعي سريع)
        # نقارن التاريخ الحالي بتاريخ الموعد + المدة
        Appointment.objects.filter(
            status='confirmed',
            date__lte=now - F('duration') * timedelta(minutes=1) 
        ).update(status='completed')