from django.apps import AppConfig

class DoctorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doctors'

    def ready(self):
        import doctors.signals # Import the signals to ensure they are registered when the app is ready
 