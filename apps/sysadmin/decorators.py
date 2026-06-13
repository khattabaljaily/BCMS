from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superuser_required(view_func):
    """Only allow is_superuser users into sysadmin views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/?next=/sysadmin/')
        if not request.user.is_superuser:
            messages.error(request, 'هذه الصفحة مخصصة لمدير النظام فقط.')
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper
