"""
CenterMiddleware — attaches the current center to every request
based on the logged-in user, and activates the tenant's timezone.
"""
import zoneinfo
from django.utils import timezone


class NoCacheMiddleware:
    """Prevent browsers from heuristically caching HTML pages."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-store'
        return response


class CenterMiddleware:
    OPEN_PATHS = (
        '/login/', '/register/', '/admin/', '/static/', '/media/', '/store/',
        '/sysadmin/', '/pricing/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.center = None

        if request.user.is_authenticated and hasattr(request.user, 'center'):
            request.center = request.user.center

        # Activate tenant timezone so all timezone.localdate()/localtime() calls
        # return dates/times in the tenant's local timezone.
        tz_name = getattr(request.center, 'timezone', None) if request.center else None
        if tz_name:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tz_name))
            except (KeyError, Exception):
                timezone.deactivate()
        else:
            timezone.deactivate()

        response = self.get_response(request)
        timezone.deactivate()
        return response
