from django.apps import AppConfig

class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appointments'
    verbose_name = 'المواعيد'
    
    def ready(self):
        # Ensure signals are registered
        try:
            import apps.appointments.signals  # noqa: F401
        except Exception:
            pass
