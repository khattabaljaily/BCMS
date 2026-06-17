import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from .forms import LoginForm, RegisterForm, PasswordResetForm, SetPasswordForm
from .models import User, Role, PERMISSIONS

SECTION_LABELS = {
    'appointments': ('المواعيد',          'fas fa-calendar-check',    '#6366f1'),
    'clients':      ('العملاء',           'fas fa-users',             '#0ea5e9'),
    'services':     ('الخدمات',           'fas fa-spa',               '#ec4899'),
    'billing':      ('الفواتير ونقطة البيع', 'fas fa-cash-register',  '#10b981'),
    'products':     ('المنتجات والمخزون', 'fas fa-boxes-stacked',     '#f59e0b'),
    'staff':        ('الفريق',            'fas fa-user-tie',          '#8b5cf6'),
    'store':        ('المتجر الإلكتروني', 'fas fa-store',             '#14b8a6'),
    'finance':      ('المالية والحسابات', 'fas fa-wallet',            '#ef4444'),
    'reports':      ('التقارير',          'fas fa-chart-bar',         '#f97316'),
    'settings':     ('الإعدادات',         'fas fa-sliders',           '#64748b'),
}


def _build_permissions_meta(instance=None):
    """Return list of section dicts for the role form template."""
    instance_perms = set()
    if instance and instance.permissions:
        instance_perms = {k for k, v in instance.permissions.items() if v}

    sections = []
    for section, actions in PERMISSIONS.items():
        lbl, icon, color = SECTION_LABELS.get(section, (section, 'fas fa-circle', '#64748b'))
        section_actions = []
        for action, label in actions.items():
            key = f'{section}.{action}'
            section_actions.append({
                'key':   key,
                'field': 'perm_' + key.replace('.', '__'),
                'label': label,
                'checked': key in instance_perms,
            })
        sections.append({
            'section':       section,
            'section_label': lbl,
            'icon':          icon,
            'color':         color,
            'actions':       section_actions,
            'all_count':     len(section_actions),
            'checked_count': sum(1 for a in section_actions if a['checked']),
        })
    return sections


def _collect_permissions(post_data):
    """Extract permission dict from POST data."""
    perms = {}
    for section, actions in PERMISSIONS.items():
        for action in actions:
            key   = f'{section}.{action}'
            field = 'perm_' + key.replace('.', '__')
            perms[key] = field in post_data
    return perms


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


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

    initial = {}
    plan_param = request.GET.get('plan', '').strip()
    if plan_param in {'starter', 'pro', 'enterprise'}:
        initial['selected_plan'] = plan_param

    form = RegisterForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('core:dashboard')

    PLAN_LABELS = {'starter': 'الأساسية', 'pro': 'الاحترافية', 'enterprise': 'المؤسسات'}
    selected_plan = request.POST.get('selected_plan') or plan_param or 'pro'
    return render(request, 'accounts/register.html', {
        'form': form,
        'selected_plan': selected_plan,
        'selected_plan_label': PLAN_LABELS.get(selected_plan, 'الاحترافية'),
    })


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('_action')
        if action == 'profile':
            try:
                user.full_name = request.POST.get('full_name', '').strip() or user.full_name
                user.phone = request.POST.get('phone', '').strip()
                user.email = request.POST.get('email', '').strip()
                user.save(update_fields=['full_name', 'phone', 'email'])
            except Exception as exc:
                if _is_ajax(request):
                    return JsonResponse({'success': False, 'error': 'تعذر حفظ البيانات.'})
                messages.error(request, 'تعذر حفظ البيانات.')
                return redirect('accounts:profile')
            if _is_ajax(request):
                return JsonResponse({'success': True, 'message': 'تم تحديث الملف الشخصي بنجاح.'})
            messages.success(request, 'تم تحديث الملف الشخصي.')
        elif action == 'password':
            current = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm_pw = request.POST.get('confirm_password', '')
            if not user.check_password(current):
                err = 'كلمة المرور الحالية غير صحيحة.'
                if _is_ajax(request):
                    return JsonResponse({'success': False, 'error': err})
                messages.error(request, err)
            elif len(new_pw) < 6:
                err = 'كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل.'
                if _is_ajax(request):
                    return JsonResponse({'success': False, 'error': err})
                messages.error(request, err)
            elif new_pw != confirm_pw:
                err = 'كلمة المرور الجديدة وتأكيدها غير متطابقتين.'
                if _is_ajax(request):
                    return JsonResponse({'success': False, 'error': err})
                messages.error(request, err)
            else:
                user.set_password(new_pw)
                user.save(update_fields=['password'])
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                if _is_ajax(request):
                    return JsonResponse({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح.'})
                messages.success(request, 'تم تغيير كلمة المرور.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': user})


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
        try:
            instance.base_salary = Decimal(data.get('base_salary') or '0')
        except Exception:
            instance.base_salary = Decimal('0')
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
        try:
            instance.save()
        except Exception as e:
            err = 'اسم الدخول مستخدم بالفعل.' if '1062' in str(e) or 'UNIQUE' in str(e).upper() else f'خطأ: {e}'
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': err}, status=400)
            messages.error(request, err)
            return render(request, 'accounts/user_form.html', {'instance': instance, 'roles': roles})
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حفظ الموظف بنجاح.'})
        messages.success(request, 'تم حفظ الموظف.')
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
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف الموظف بنجاح.'})
        messages.success(request, 'تم حذف الموظف.')
    return redirect('accounts:users')


@login_required
def role_list(request):
    center = request.center
    roles = Role.objects.filter(center=center).annotate(user_count=models.Count('users'))
    return render(request, 'accounts/roles.html', {'roles': roles})


@login_required
def role_save(request, pk=None):
    center = request.center
    instance = get_object_or_404(Role, pk=pk, center=center) if pk else None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'اسم الدور مطلوب.')
            return render(request, 'accounts/role_form.html', {
                'instance': instance,
                'permissions_meta': _build_permissions_meta(instance),
            })
        if instance is None:
            instance = Role(center=center)
        instance.name = name
        instance.permissions = _collect_permissions(request.POST)
        instance.is_default = 'is_default' in request.POST
        try:
            instance.save()
        except Exception as e:
            err = 'يوجد دور بهذا الاسم بالفعل.' if '1062' in str(e) or 'UNIQUE' in str(e).upper() else f'خطأ: {e}'
            if _is_ajax(request):
                return JsonResponse({'success': False, 'message': err}, status=400)
            messages.error(request, err)
            return render(request, 'accounts/role_form.html', {'instance': instance, 'permissions_meta': _build_permissions_meta(instance)})
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حفظ الدور بنجاح.'})
        messages.success(request, 'تم حفظ الدور.')
        return redirect('accounts:roles')

    total_perms = sum(len(actions) for actions in PERMISSIONS.values())
    return render(request, 'accounts/role_form.html', {
        'instance': instance,
        'permissions_meta': _build_permissions_meta(instance),
        'total_perms': total_perms,
    })


@login_required
def role_delete(request, pk):
    center = request.center
    role = get_object_or_404(Role, pk=pk, center=center)
    if request.method == 'POST':
        role.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف الدور.'})
        messages.success(request, 'تم حذف الدور.')
    return redirect('accounts:roles')


def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            subject = 'إعادة تعيين كلمة المرور - BCMS'
            html_message = render_to_string('accounts/email/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })
            try:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=html_message,
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, 'تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني.')
            except Exception:
                messages.error(request, 'حدث خطأ في إرسال البريد الإلكتروني. يرجى المحاولة لاحقاً.')
    else:
        form = PasswordResetForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'رابط إعادة التعيين غير صحيح أو منتهي الصلاحية.')
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save(update_fields=['password'])
            messages.success(request, 'تم تغيير كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.')
            return redirect('accounts:login')
    else:
        form = SetPasswordForm()

    return render(request, 'accounts/password_reset_confirm.html', {'form': form})


def password_reset_complete(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'accounts/password_reset_complete.html')
