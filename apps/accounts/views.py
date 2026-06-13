import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm
from .models import User, Role
from .permissions import PERMISSIONS


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('sysadmin:dashboard')
        return redirect('core:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        login(request, user)
        if user.is_superuser:
            return redirect('sysadmin:dashboard')
        return redirect(request.GET.get('next') or 'core:dashboard')

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('core:dashboard')

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def user_list(request):
    center = request.center
    qs = User.objects.filter(center=center).order_by('-created_at')

    q = request.GET.get('q', '').strip()
    role = request.GET.get('role')
    if q:
        qs = qs.filter(
            models.Q(full_name__icontains=q) |
            models.Q(username__icontains=q) |
            models.Q(phone__icontains=q) |
            models.Q(email__icontains=q)
        )
    if role:
        try:
            role_pk = int(role)
            qs = qs.filter(role_id=role_pk)
        except Exception:
            pass

    roles = Role.objects.filter(center=center)
    return render(request, 'accounts/users.html', {'users': qs, 'roles': roles, 'q': q, 'role_filter': role})


@login_required
def user_save(request, pk=None):
    center = request.center
    instance = get_object_or_404(User, pk=pk, center=center) if pk else None
    roles = Role.objects.filter(center=center)

    if request.method == 'POST':
        data = request.POST
        if instance is None:
            instance = User(center=center)
            instance.username = data.get('username').strip()
        instance.full_name = data.get('full_name', '').strip()
        instance.phone = data.get('phone', '').strip()
        instance.email = data.get('email', '').strip()
        role_id = data.get('role') or None
        # validate role belongs to center
        if role_id:
            try:
                role_obj = Role.objects.get(pk=int(role_id), center=center)
                instance.role = role_obj
            except Exception:
                instance.role = None
        else:
            instance.role = None
        instance.is_active = 'is_active' in data
        instance.is_staff = 'is_staff' in data
        if data.get('password'):
            instance.set_password(data.get('password'))
        instance.save()
        messages.success(request, 'تم حفظ المستخدم.')
        return redirect('accounts:users')

    return render(request, 'accounts/user_form.html', {
        'instance': instance,
        'roles': roles,
    })


@login_required
def user_delete(request, pk):
    center = request.center
    obj = get_object_or_404(User, pk=pk, center=center)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'تم حذف المستخدم.')
    return redirect('accounts:users')


@login_required
def role_list(request):
    center = request.center
    roles = Role.objects.filter(center=center)
    return render(request, 'accounts/roles.html', {'roles': roles})


@login_required
def role_save(request, pk=None):
    center = request.center
    instance = get_object_or_404(Role, pk=pk, center=center) if pk else None

    # build permission metadata for template
    permissions_meta = [
        {
            'key': p,
            'field': 'perm_' + p.replace('.', '__'),
            'label': p,
        }
        for p in PERMISSIONS
    ]

    # existing permissions for the instance (list of keys where value is truthy)
    instance_perms = []
    if instance and instance.permissions:
        try:
            instance_perms = [k for k, v in instance.permissions.items() if v]
        except Exception:
            instance_perms = []

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        perms = {}
        for p in PERMISSIONS:
            field = 'perm_' + p.replace('.', '__')
            perms[p] = field in request.POST

        if instance is None:
            instance = Role(center=center)
        instance.name = name
        instance.permissions = perms
        instance.is_default = 'is_default' in request.POST
        instance.save()
        messages.success(request, 'تم حفظ الدور.')
        return redirect('accounts:roles')

    return render(request, 'accounts/role_form.html', {
        'instance': instance,
        'permissions_meta': permissions_meta,
        'instance_perms': instance_perms,
    })
