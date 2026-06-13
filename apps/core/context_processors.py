from apps.core.models import Settings


def center_context(request):
    ctx = {
        'center': getattr(request, 'center', None),
        'center_settings': None,
    }
    center = ctx['center']
    if center:
        settings_obj, _ = Settings.objects.get_or_create(center=center)
        ctx['center_settings'] = settings_obj
        # lightweight pending counters for nav badges
        try:
            from apps.store.models import OnlineBooking, StoreOrder
            ctx['pending_bookings'] = OnlineBooking.objects.filter(center=center, status='new').count()
            ctx['pending_orders'] = StoreOrder.objects.filter(center=center, status='pending').count()
        except Exception:
            ctx['pending_bookings'] = 0
            ctx['pending_orders'] = 0
    else:
        ctx['pending_bookings'] = 0
        ctx['pending_orders'] = 0
    return ctx
