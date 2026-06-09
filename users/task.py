from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from users.models import User
import logging

logger = logging.getLogger(__name__)

@shared_task
def delete_unverified_users():
    cutoff = timezone.now() - timedelta(hours=24)  # بعد 24 ساعة من التسجيل
    
    qs = User.objects.filter(
        is_verified=False,
        date_joined__lt=cutoff
    )
    count, _ = qs.delete()
    logger.info(f"Deleted {count} unverified users")
    return count