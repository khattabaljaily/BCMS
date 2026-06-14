from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StockMovement


@receiver(post_save, sender=StockMovement)
def stock_low_notification(sender, instance, created, **kwargs):
    if not created:
        return
    product = instance.product
    if product.stock > product.min_stock:
        return
    from apps.core.notifications import notify
    notify(
        center=instance.center,
        type='stock_low',
        title=f'مخزون منخفض: {product.name}',
        body=f'الكمية المتبقية: {product.stock} (الحد الأدنى: {product.min_stock})',
        url='/products/stock/',
        dedupe_hours=24,
    )
