from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OnlineBooking, StoreOrder


@receiver(post_save, sender=OnlineBooking)
def booking_new_notification(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.core.notifications import notify
    service_label = str(getattr(instance.service, 'name', '') or '')
    date_label    = str(instance.preferred_date or '')
    body_parts    = [p for p in [service_label, date_label] if p]
    notify(
        center=instance.center,
        type='booking_new',
        title=f'حجز أونلاين جديد: {instance.client_name}',
        body=' — '.join(body_parts),
        url='/store/manage/bookings/',
    )


@receiver(post_save, sender=StoreOrder)
def order_new_notification(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.core.notifications import notify
    notify(
        center=instance.center,
        type='order_new',
        title=f'طلب أونلاين جديد: {instance.client_name}',
        body=f'الإجمالي: {instance.total}',
        url='/store/manage/orders/',
    )
