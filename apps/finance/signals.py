"""
Finance app signals.
Auto-create Treasury for new Centers (tenants).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.core.models import Center
from .models import Treasury


@receiver(post_save, sender=Center)
def create_center_treasury(sender, instance, created, **kwargs):
    """Create default treasury when a new Center is registered."""
    if created:
        Treasury.objects.get_or_create(
            center=instance,
            defaults={
                'name': 'الخزينة الرئيسية',
                'initial_balance': 0,
                'balance': 0,
            }
        )
