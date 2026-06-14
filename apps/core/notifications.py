"""
Central helper for creating notifications.
Call notify() from anywhere — views, signals, management commands.
Silently no-ops on errors so it never breaks the calling flow.
"""
from django.utils import timezone
from datetime import timedelta


def notify(center, type, title, body='', url='', dedupe_hours=0):
    """
    Create a notification for a center.

    dedupe_hours: if > 0, skip creation if an unread notification of the same
    type with the same title already exists within that many hours (prevents spam).
    """
    try:
        from apps.core.models import Notification
        if dedupe_hours:
            cutoff = timezone.now() - timedelta(hours=dedupe_hours)
            if Notification.objects.filter(
                center=center,
                type=type,
                title=title,
                is_read=False,
                created_at__gte=cutoff,
            ).exists():
                return
        Notification.objects.create(
            center=center,
            type=type,
            title=title,
            body=body,
            url=url,
        )
    except Exception:
        pass
