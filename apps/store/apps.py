from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.store'
    verbose_name = 'المتجر'

    def ready(self):
        try:
            import apps.store.signals  # noqa: F401
        except Exception:
            pass
