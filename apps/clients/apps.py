from django.apps import AppConfig

class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
    verbose_name = 'العملاء'

    def ready(self):
        try:
            import apps.clients.signals  # noqa: F401
        except Exception:
            pass
