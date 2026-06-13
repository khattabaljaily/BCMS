from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finance'
    verbose_name = 'المالية'

    def ready(self):
        """Register signals when the app is ready."""
        from . import signals  # noqa
