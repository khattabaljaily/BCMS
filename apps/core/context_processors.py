from apps.core.models import Settings


def help_context(request):
    """Inject the help template path for the current page."""
    try:
        match = request.resolver_match
        if not match or not match.namespace or not match.url_name:
            return {'help_template': None}
        candidate = f"help/{match.namespace}/{match.url_name}.html"
        from django.template.loader import get_template
        from django.template import TemplateDoesNotExist
        try:
            get_template(candidate)
            return {'help_template': candidate}
        except TemplateDoesNotExist:
            return {'help_template': None}
    except Exception:
        return {'help_template': None}


def center_context(request):
    ctx = {
        'center': getattr(request, 'center', None),
        'center_settings': None,
        'pending_support_count': 0,
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

    # Sysadmin: count open/in_progress support tickets for sidebar badge
    if getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_superuser:
        try:
            from apps.core.models import SupportTicket
            ctx['pending_support_count'] = SupportTicket.objects.filter(
                status__in=['open', 'in_progress']
            ).count()
        except Exception:
            pass

    return ctx
