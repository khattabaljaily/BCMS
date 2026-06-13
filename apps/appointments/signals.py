from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.appointments.models import Appointment
from apps.billing.models import Invoice


@receiver(post_save, sender=Appointment)
def create_invoice_on_confirm(sender, instance, created, **kwargs):
    # When an appointment becomes confirmed, create a linked invoice if none exists.
    try:
        has_invoice = getattr(instance, 'invoice', None)
    except Invoice.DoesNotExist:
        has_invoice = None

    if instance.status == 'confirmed' and not has_invoice:
        # Delay import of Settings to avoid circular imports at module import time
        from apps.core.models import Settings
        settings_obj, _ = Settings.objects.get_or_create(center=instance.center)
        number = settings_obj.next_invoice_number()
        Invoice.objects.create(
            center=instance.center,
            number=number,
            client=instance.client,
            appointment=instance,
            payment_method='cash',
            status='draft',
        )
