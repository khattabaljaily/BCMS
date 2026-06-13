"""
BCMS SysAdmin — system-level views for managing all tenants/centers.
Accessible only to is_superuser users.
"""
import json
from datetime import timedelta, date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.http import require_POST

from apps.core.models import Center, ServiceType, Settings, CenterBackup
from apps.core.countries import ARAB_COUNTRIES, COUNTRY_CHOICES
from apps.accounts.models import User
from .decorators import superuser_required



# ── Dashboard ─────────────────────────────────────────────────────────────────

@superuser_required
def dashboard(request):
    today = timezone.localdate()

    total_centers  = Center.objects.count()
    active_centers = Center.objects.filter(is_active=True).count()
    trial_centers  = Center.objects.filter(plan='trial').count()
    expired_centers = Center.objects.filter(
        plan_expires__lt=today, is_active=True
    ).count()

    plans_data = (
        Center.objects
        .values('plan')
        .annotate(count=Count('id'))
        .order_by('plan')
    )
    PLAN_LABELS = {
        'trial': 'تجريبي', 'starter': 'مبتدئ',
        'pro': 'احترافي', 'enterprise': 'مؤسسات',
    }
    PLAN_COLORS = {
        'trial': '#94a3b8', 'starter': '#3b82f6',
        'pro': '#8b5cf6', 'enterprise': '#f59e0b',
    }
    chart_plan_labels = [PLAN_LABELS.get(r['plan'], r['plan']) for r in plans_data]
    chart_plan_data   = [r['count'] for r in plans_data]
    chart_plan_colors = [PLAN_COLORS.get(r['plan'], '#94a3b8') for r in plans_data]

    # registrations last 30 days
    thirty_ago = today - timedelta(days=29)
    reg_rows = (
        Center.objects
        .filter(created_at__date__gte=thirty_ago)
        .extra(select={'day': 'DATE(created_at)'})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    reg_map = {}
    for r in reg_rows:
        d = r['day']
        if isinstance(d, str):
            d = date.fromisoformat(d)
        reg_map[d] = r['count']

    chart_reg_labels, chart_reg_data = [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        chart_reg_labels.append(d.strftime('%d/%m'))
        chart_reg_data.append(reg_map.get(d, 0))

    recent_centers = (
        Center.objects
        .select_related('service_type')
        .order_by('-created_at')[:8]
    )

    expiring_soon = (
        Center.objects
        .filter(
            plan_expires__gte=today,
            plan_expires__lte=today + timedelta(days=14),
            is_active=True,
        )
        .order_by('plan_expires')[:6]
    )

    total_users = User.objects.filter(center__isnull=False).count()

    return render(request, 'sysadmin/dashboard.html', {
        'total_centers':   total_centers,
        'active_centers':  active_centers,
        'inactive_centers': total_centers - active_centers,
        'trial_centers':   trial_centers,
        'expired_centers': expired_centers,
        'total_users':     total_users,
        'recent_centers':  recent_centers,
        'expiring_soon':   expiring_soon,
        'chart_plan_labels': json.dumps(chart_plan_labels),
        'chart_plan_data':   json.dumps(chart_plan_data),
        'chart_plan_colors': json.dumps(chart_plan_colors),
        'chart_reg_labels':  json.dumps(chart_reg_labels),
        'chart_reg_data':    json.dumps(chart_reg_data),
        'today': today,
    })


# ── Centers ───────────────────────────────────────────────────────────────────

@superuser_required
def center_list(request):
    qs = Center.objects.select_related('service_type').order_by('-created_at')

    q      = request.GET.get('q', '').strip()
    plan   = request.GET.get('plan', '')
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(phone__icontains=q) |
            Q(email__icontains=q) | Q(city__icontains=q)
        )
    if plan:
        qs = qs.filter(plan=plan)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'expired':
        qs = qs.filter(plan_expires__lt=timezone.localdate(), is_active=True)

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    per_page = 20
    total    = qs.count()
    centers  = qs[(page - 1) * per_page: page * per_page]
    total_pages = (total + per_page - 1) // per_page

    return render(request, 'sysadmin/centers.html', {
        'centers':        centers,
        'q':              q,
        'plan':           plan,
        'status':         status,
        'page':           page,
        'total_pages':    total_pages,
        'total':          total,
        'plans':          Center.PLANS,
        'service_types':  ServiceType.objects.filter(is_active=True).order_by('order', 'name'),
        'country_choices': COUNTRY_CHOICES,
        'arab_countries_json': json.dumps({
            k: {'tz': v['timezone'], 'cur': v['currency']}
            for k, v in ARAB_COUNTRIES.items()
        }),
    })


@superuser_required
def center_detail(request, pk):
    center = get_object_or_404(Center.objects.select_related('service_type'), pk=pk)
    users  = User.objects.filter(center=center).order_by('-created_at')
    today  = timezone.localdate()

    return render(request, 'sysadmin/center_detail.html', {
        'center': center,
        'users':  users,
        'today':  today,
        'plans':  Center.PLANS,
    })


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _center_payload(c):
    """Return serialisable dict for a center row (used in AJAX responses)."""
    return {
        'pk':                c.pk,
        'name':              c.name,
        'slug':              c.slug,
        'phone':             c.phone,
        'email':             c.email,
        'address':           c.address,
        'city':              c.city,
        'country':           c.country,
        'service_type_id':   c.service_type_id or '',
        'service_type_name': c.service_type.name if c.service_type else '',
        'plan':              c.plan,
        'plan_expires':      c.plan_expires.strftime('%Y-%m-%d') if c.plan_expires else '',
        'max_staff':         c.max_staff,
        'max_users':         c.max_users,
        'is_active':         c.is_active,
        'is_demo':           c.is_demo,
        'created_at':        c.created_at.strftime('%d/%m/%Y'),
    }


def _service_type_payload(t):
    return {
        'pk':          t.pk,
        'name':        t.name,
        'icon':        t.icon,
        'color':       t.color,
        'description': t.description,
        'order':       t.order,
        'is_active':   t.is_active,
    }


@superuser_required
def center_add(request):
    service_types = ServiceType.objects.filter(is_active=True).order_by('order', 'name')
    ajax = _is_ajax(request)

    if request.method == 'POST':
        name            = request.POST.get('name', '').strip()
        slug            = request.POST.get('slug', '').strip()
        phone           = request.POST.get('phone', '').strip()
        email           = request.POST.get('email', '').strip()
        address         = request.POST.get('address', '').strip()
        city            = request.POST.get('city', '').strip()
        country_code    = request.POST.get('country', 'SD').strip()
        plan            = request.POST.get('plan', 'trial')
        plan_expires    = request.POST.get('plan_expires') or None
        service_type_id = request.POST.get('service_type')
        max_staff       = int(request.POST.get('max_staff', 10) or 10)
        max_users       = int(request.POST.get('max_users', 5) or 5)
        is_active       = bool(request.POST.get('is_active'))
        is_demo         = bool(request.POST.get('is_demo'))

        country_info = ARAB_COUNTRIES.get(country_code, ARAB_COUNTRIES['SD'])

        if not name or not slug:
            err = 'اسم المركز والرابط المختصر مطلوبان.'
            if ajax: return JsonResponse({'success': False, 'error': err})
            messages.error(request, err)
        elif Center.objects.filter(slug=slug).exists():
            err = 'هذا الرابط المختصر مستخدم بالفعل.'
            if ajax: return JsonResponse({'success': False, 'error': err})
            messages.error(request, err)
        else:
            st = get_object_or_404(ServiceType, pk=service_type_id) if service_type_id else None
            c = Center.objects.create(
                name=name, slug=slug, phone=phone, email=email,
                address=address, city=city, plan=plan,
                country=country_code,
                timezone=country_info['timezone'],
                currency=country_info['currency'],
                plan_expires=plan_expires, service_type=st,
                max_staff=max_staff, max_users=max_users,
                is_active=is_active, is_demo=is_demo,
            )
            Settings.objects.get_or_create(center=c)
            if ajax:
                return JsonResponse({'success': True, 'center': _center_payload(c)})
            messages.success(request, f'تم إنشاء المركز "{name}" بنجاح.')
            return redirect('sysadmin:center_detail', pk=c.pk)

    return render(request, 'sysadmin/center_form.html', {
        'service_types':   service_types,
        'plans':           Center.PLANS,
        'country_choices': COUNTRY_CHOICES,
        'obj':             None,
    })


@superuser_required
def center_edit(request, pk):
    center = get_object_or_404(Center, pk=pk)
    service_types = ServiceType.objects.filter(is_active=True).order_by('order', 'name')
    ajax = _is_ajax(request)

    if request.method == 'POST':
        center.name    = request.POST.get('name', '').strip() or center.name
        center.phone   = request.POST.get('phone', '').strip()
        center.email   = request.POST.get('email', '').strip()
        center.address = request.POST.get('address', '').strip()
        center.city    = request.POST.get('city', '').strip()
        center.plan    = request.POST.get('plan', center.plan)
        center.plan_expires = request.POST.get('plan_expires') or None
        center.max_staff = int(request.POST.get('max_staff', center.max_staff) or center.max_staff)
        center.max_users = int(request.POST.get('max_users', center.max_users) or center.max_users)
        center.is_active = bool(request.POST.get('is_active'))
        center.is_demo   = bool(request.POST.get('is_demo'))
        country_code = request.POST.get('country', center.country).strip()
        if country_code in ARAB_COUNTRIES:
            country_info = ARAB_COUNTRIES[country_code]
            center.country   = country_code
            center.timezone  = country_info['timezone']
            center.currency  = country_info['currency']
        st_id = request.POST.get('service_type')
        if st_id:
            center.service_type_id = int(st_id)
        if 'logo' in request.FILES:
            center.logo = request.FILES['logo']
        center.save()
        if ajax:
            return JsonResponse({'success': True, 'center': _center_payload(center)})
        messages.success(request, 'تم حفظ بيانات المركز.')
        return redirect('sysadmin:center_detail', pk=center.pk)

    return render(request, 'sysadmin/center_form.html', {
        'service_types':   service_types,
        'plans':           Center.PLANS,
        'country_choices': COUNTRY_CHOICES,
        'obj':             center,
    })


@superuser_required
def center_toggle(request, pk):
    if request.method == 'POST':
        center = get_object_or_404(Center, pk=pk)
        center.is_active = not center.is_active
        center.save(update_fields=['is_active'])
        if _is_ajax(request):
            return JsonResponse({'success': True, 'is_active': center.is_active})
        state = 'تم تفعيل' if center.is_active else 'تم إيقاف'
        messages.success(request, f'{state} المركز "{center.name}".')
    return redirect(request.POST.get('next', 'sysadmin:center_list'))


@superuser_required
def center_extend(request, pk):
    """Extend or change plan."""
    if request.method == 'POST':
        center = get_object_or_404(Center, pk=pk)
        new_plan    = request.POST.get('plan', center.plan)
        new_expires = request.POST.get('plan_expires') or None
        center.plan = new_plan
        center.plan_expires = new_expires
        center.save(update_fields=['plan', 'plan_expires'])
        messages.success(request, 'تم تحديث الاشتراك بنجاح.')
    return redirect('sysadmin:center_detail', pk=pk)


@superuser_required
def center_delete(request, pk):
    if request.method == 'POST':
        center = get_object_or_404(Center, pk=pk)
        name = center.name
        center.delete()
        messages.success(request, f'تم حذف المركز "{name}".')
    return redirect('sysadmin:center_list')


# ── Service Types ─────────────────────────────────────────────────────────────

@superuser_required
def service_types(request):
    types = ServiceType.objects.all().order_by('order', 'name')
    return render(request, 'sysadmin/service_types.html', {'types': types})


@superuser_required
def service_type_save(request, pk=None):
    obj = get_object_or_404(ServiceType, pk=pk) if pk else None

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        icon        = request.POST.get('icon', 'fas fa-spa').strip()
        color       = request.POST.get('color', '#ec4899').strip()
        description = request.POST.get('description', '').strip()
        order       = int(request.POST.get('order', 0) or 0)
        is_active   = bool(request.POST.get('is_active'))

        if not name:
            messages.error(request, 'الاسم مطلوب.')
        else:
            if obj:
                obj.name = name; obj.icon = icon; obj.color = color
                obj.description = description; obj.order = order
                obj.is_active = is_active
                obj.save()
                messages.success(request, 'تم تعديل نوع المركز.')
            else:
                ServiceType.objects.create(
                    name=name, icon=icon, color=color,
                    description=description, order=order, is_active=is_active,
                )
                messages.success(request, 'تم إضافة نوع المركز.')
        return redirect('sysadmin:service_types')

    return render(request, 'sysadmin/service_type_form.html', {'obj': obj})


@superuser_required
def service_type_delete(request, pk):
    if request.method == 'POST':
        obj = get_object_or_404(ServiceType, pk=pk)
        if obj.centers.exists():
            messages.error(request, 'لا يمكن حذف نوع مرتبط بمراكز موجودة.')
        else:
            obj.delete()
            messages.success(request, 'تم حذف نوع المركز.')
    return redirect('sysadmin:service_types')


# ── Backup & Restore ──────────────────────────────────────────────────────────

@superuser_required
def backup_list(request):
    from .backup_service import get_center_backup_stats

    centers = Center.objects.order_by('name')
    center_rows = []
    total_backups = 0
    total_size = 0

    for center in centers:
        stats = get_center_backup_stats(center)
        total_backups += stats['total']
        total_size += stats['total_size']
        center_rows.append({
            'center':     center,
            'count':      stats['total'],
            'total_size': stats['total_size'],
            'latest':     stats['latest'],
        })

    return render(request, 'sysadmin/backup.html', {
        'center_rows':       center_rows,
        'centers_count':     centers.count(),
        'total_backups':     total_backups,
        'total_size':        total_size,
        'centers_no_backup': sum(1 for r in center_rows if r['count'] == 0),
    })


@superuser_required
def backup_detail(request, pk):
    center  = get_object_or_404(Center, pk=pk)
    backups = CenterBackup.objects.filter(center=center).order_by('-created_at')
    total_size = sum(b.file_size for b in backups if b.status == 'completed')

    return render(request, 'sysadmin/backup_detail.html', {
        'center':     center,
        'backups':    backups,
        'total_size': total_size,
    })


@require_POST
@superuser_required
def backup_create_api(request, pk):
    from .backup_service import create_backup

    center = get_object_or_404(Center, pk=pk)
    record = create_backup(center, backup_type='manual')
    if record.status == 'completed':
        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء نسخة احتياطية بنجاح ({record.file_size_display})',
            'backup': {
                'id':       record.pk,
                'filename': record.filename,
                'size':     record.file_size_display,
                'type':     record.get_backup_type_display(),
            },
        })
    return JsonResponse({'success': False, 'message': 'فشل إنشاء النسخة الاحتياطية'}, status=500)


@require_POST
@superuser_required
def backup_restore_api(request, backup_id):
    from .backup_service import restore_backup

    success, message = restore_backup(backup_id)
    return JsonResponse({'success': success, 'message': message},
                        status=200 if success else 500)


@require_POST
@superuser_required
def backup_delete_api(request, backup_id):
    from .backup_service import delete_backup

    success, message = delete_backup(backup_id)
    return JsonResponse({'success': success, 'message': message},
                        status=200 if success else 500)


@superuser_required
def backup_download(request, backup_id):
    from pathlib import Path
    backup = get_object_or_404(CenterBackup, pk=backup_id, status='completed')
    file_path = Path(backup.file_path)
    if not file_path.exists():
        raise Http404("ملف النسخة الاحتياطية غير موجود")
    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=backup.filename,
    )


# ── Users overview ────────────────────────────────────────────────────────────

@superuser_required
def users_overview(request):
    qs = (
        User.objects
        .filter(center__isnull=False)
        .select_related('center', 'role')
        .order_by('-created_at')
    )
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(full_name__icontains=q) | Q(username__icontains=q) |
            Q(center__name__icontains=q)
        )

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    per_page = 30
    total = qs.count()
    users = qs[(page - 1) * per_page: page * per_page]
    total_pages = (total + per_page - 1) // per_page

    return render(request, 'sysadmin/users.html', {
        'users': users,
        'q': q,
        'page': page,
        'total_pages': total_pages,
        'total': total,
    })
