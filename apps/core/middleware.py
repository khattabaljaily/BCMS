"""
CenterMiddleware — attaches the current center to every request
based on the logged-in user, and activates the tenant's timezone.
"""
import zoneinfo
from django.utils import timezone
from django.shortcuts import render, redirect


class MaintenanceMiddleware:
    BYPASS_PATHS = ('/sysadmin/', '/static/', '/media/', '/favicon', '/login/', '/logout/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Superusers always pass through
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)
        # Sysadmin and static paths always pass through
        if any(path.startswith(p) for p in self.BYPASS_PATHS):
            return self.get_response(request)
        # Lazy-import to avoid app-registry issues at startup
        try:
            from apps.core.models import PlatformSettings
            ps = PlatformSettings.get()
            if ps.maintenance_mode:
                return render(request, 'maintenance.html',
                              {'message': ps.maintenance_message}, status=503)
        except Exception:
            pass
        return self.get_response(request)


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
        '/sysadmin/', '/pricing/', '/about/', '/subscription/', '/support/',
        '/logout/',
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

        # Block access for expired or inactive centers
        if (
            request.user.is_authenticated
            and not request.user.is_superuser
            and request.center is not None
            and not any(request.path.startswith(p) for p in self.OPEN_PATHS)
        ):
            if not request.center.is_active or request.center.is_expired:
                response = self.get_response(request)
                timezone.deactivate()
                return redirect('/subscription/')

        response = self.get_response(request)
        timezone.deactivate()
        return response
