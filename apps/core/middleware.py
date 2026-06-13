"""
CenterMiddleware — attaches the current center to every request
based on the logged-in user.
"""
from django.shortcuts import redirect
from django.urls import reverse


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
        '/sysadmin/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.center = None

        if request.user.is_authenticated and hasattr(request.user, 'center'):
            request.center = request.user.center

        response = self.get_response(request)
        return response
