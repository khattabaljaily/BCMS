from django.apps import AppConfig

class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'المنتجات'

    def ready(self):
        try:
            import apps.products.signals  # noqa: F401
        except Exception:
            pass
