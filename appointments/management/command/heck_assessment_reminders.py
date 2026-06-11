# appointments/management/commands/check_assessment_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from assessments.utils import enable_assessment_for_patient

class Command(BaseCommand):
    help = 'Activates assessment for patients whose last session was 10 days ago.'

    def handle(self, *args, **options):
        ten_days_ago = timezone.now() - timedelta(days=10)
        
        # Fetch completed appointments from 10 days ago with no next session
        expired_sessions = Appointment.objects.filter(
            status=Appointment.Status.Completed,
            date__lte=ten_days_ago,
            has_next_session=False
        )

        count = 0
        for appointment in expired_sessions:
            enable_assessment_for_patient(appointment.patient)
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully enabled assessments for {count} patients.'))