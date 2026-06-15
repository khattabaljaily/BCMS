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
        'trial': 'تجريبي', 'starter': 'أساسي',
        'pro': 'متقدم', 'enterprise': 'أعمال',
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
        'center':          center,
        'users':           users,
        'today':           today,
        'plans':           Center.PLANS,
        'service_types':   ServiceType.objects.filter(is_active=True).order_by('order', 'name'),
        'country_choices': COUNTRY_CHOICES,
    })


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _center_payload(c):
    """Return serialisable dict for a center row (used in AJAX responses)."""
    from datetime import date, datetime
    
    # Helper to format dates (handle both datetime objects and strings)
    def fmt_date(d, fmt='%Y-%m-%d'):
        if not d:
            return ''
        if isinstance(d, str):
            return d
        if isinstance(d, (datetime, date)):
            return d.strftime(fmt)
        return str(d)
    
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
        'plan_expires':      fmt_date(c.plan_expires),
        'max_staff':         c.max_staff,
        'max_users':         c.max_users,
        'is_active':         c.is_active,
        'is_demo':           c.is_demo,
        'created_at':        fmt_date(c.created_at, '%d/%m/%Y'),
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

        # Owner fields (for new centers)
        owner_full_name = request.POST.get('owner_full_name', '').strip()
        owner_username  = request.POST.get('owner_username', '').strip()
        owner_password  = request.POST.get('owner_password', '').strip()
        owner_password2 = request.POST.get('owner_password2', '').strip()

        country_info = ARAB_COUNTRIES.get(country_code, ARAB_COUNTRIES['SD'])

        # Validation
        errors = []
        if not name or not slug:
            errors.append('اسم الحساب والرابط المختصر مطلوبان.')
        if Center.objects.filter(slug=slug).exists():
            errors.append('هذا الرابط المختصر مستخدم بالفعل.')
        if not owner_full_name:
            errors.append('اسم المالك مطلوب.')
        if not owner_username:
            errors.append('اسم المستخدم مطلوب.')
        elif User.objects.filter(username=owner_username).exists():
            errors.append('اسم المستخدم مستخدم بالفعل.')
        if not owner_password:
            errors.append('كلمة المرور مطلوبة.')
        elif len(owner_password) < 6:
            errors.append('كلمة المرور يجب أن تكون 6 أحرف على الأقل.')
        if owner_password != owner_password2:
            errors.append('كلمة المرور وتأكيدها غير متطابقتين.')

        if errors:
            if ajax:
                return JsonResponse({'success': False, 'error': ' | '.join(errors)})
            for err in errors:
                messages.error(request, err)
        else:
            try:
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

                # Create owner user
                owner = User.objects.create_user(
                    username=owner_username,
                    password=owner_password,
                    full_name=owner_full_name,
                    center=c,
                    is_owner=True,
                )

                if ajax:
                    return JsonResponse({
                        'success': True,
                        'center': _center_payload(c),
                        'owner_username': owner_username,
                        'owner_full_name': owner_full_name,
                    })
                messages.success(request, f'تم إنشاء الحساب "{name}" بنجاح. بيانات الدخول: المستخدم "{owner_username}".')
                return redirect('sysadmin:center_detail', pk=c.pk)
            except Exception as e:
                import logging
                logging.exception("Error creating center")
                if ajax:
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {e}')

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
        try:
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
            messages.success(request, 'تم حفظ بيانات الحساب.')
            return redirect('sysadmin:center_detail', pk=center.pk)
        except Exception as e:
            import logging
            logging.exception("Error editing center %s", pk)
            if ajax:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {e}')
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
        messages.success(request, f'{state} الحساب "{center.name}".')
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


def _force_delete_center(center):
    """
    Delete a center and ALL its data, bypassing on_delete=PROTECT constraints.

    Django raises ProtectedError even when the referencing object is itself in the
    deletion set, so we pre-delete every PROTECT-protected object explicitly in the
    correct dependency order before calling center.delete().

    PROTECT relationships in this codebase:
      Appointment.client       → Client       (PROTECT)
      Invoice.client           → Client       (PROTECT)
      AppointmentService.service → Service    (PROTECT)
      Product.category         → ProductCategory (PROTECT)
      PurchaseInvoiceLine.product → Product   (PROTECT)
      StoreOrderItem.product   → Product      (PROTECT)
    """
    from django.db import transaction

    with transaction.atomic():
        # ── Step 1: break PROTECT on Service ──────────────────────────────
        from apps.appointments.models import AppointmentService
        AppointmentService.objects.filter(appointment__center=center).delete()

        # ── Step 2: break PROTECT on Client ───────────────────────────────
        from apps.billing.models import InvoiceLine, Invoice
        from apps.finance.models import ClientPayment, TreasuryMovement
        from apps.appointments.models import Appointment

        InvoiceLine.objects.filter(invoice__center=center).delete()
        ClientPayment.objects.filter(center=center).delete()
        Invoice.objects.filter(center=center).delete()
        Appointment.objects.filter(center=center).delete()

        # ── Step 3: break PROTECT on Product ──────────────────────────────
        from apps.store.models import StoreOrderItem
        from apps.products.models import PurchaseInvoiceLine, StockMovement, Product

        StoreOrderItem.objects.filter(order__center=center).delete()
        PurchaseInvoiceLine.objects.filter(invoice__center=center).delete()
        StockMovement.objects.filter(center=center).delete()

        # Product.category → ProductCategory (PROTECT): delete products so
        # ProductCategory can be cascade-deleted together with Center.
        Product.objects.filter(center=center).delete()

        # ── Step 4: cleanup treasury movements (CASCADE anyway) ────────────
        TreasuryMovement.objects.filter(treasury__center=center).delete()

        # ── Step 5: all PROTECT blocks cleared — cascade the rest ──────────
        center.delete()


@superuser_required
def center_delete(request, pk):
    if request.method == 'POST':
        center = get_object_or_404(Center, pk=pk)
        name = center.name
        try:
            _force_delete_center(center)
        except Exception as e:
            import logging
            logging.exception("Error force-deleting center %s", pk)
            if _is_ajax(request):
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'حدث خطأ أثناء حذف الحساب: {e}')
            return redirect('sysadmin:center_detail', pk=pk)

        if _is_ajax(request):
            return JsonResponse({'success': True})
        messages.success(request, f'تم حذف الحساب "{name}" وجميع بياناته.')
    return redirect('sysadmin:center_list')


# ── Service Types ─────────────────────────────────────────────────────────────

@superuser_required
def service_types(request):
    types = ServiceType.objects.all().order_by('order', 'name')
    return render(request, 'sysadmin/service_types.html', {'types': types})


@superuser_required
def service_type_save(request, pk=None):
    obj  = get_object_or_404(ServiceType, pk=pk) if pk else None
    ajax = _is_ajax(request)

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        icon        = request.POST.get('icon', 'fas fa-spa').strip()
        color       = request.POST.get('color', '#ec4899').strip()
        description = request.POST.get('description', '').strip()
        order       = int(request.POST.get('order', 0) or 0)
        is_active   = bool(request.POST.get('is_active'))

        if not name:
            err = 'الاسم مطلوب.'
            if ajax:
                return JsonResponse({'success': False, 'error': err})
            messages.error(request, err)
        else:
            if obj:
                obj.name = name; obj.icon = icon; obj.color = color
                obj.description = description; obj.order = order
                obj.is_active = is_active
                obj.save()
                if ajax:
                    return JsonResponse({'success': True, 'type': _service_type_payload(obj)})
                messages.success(request, 'تم تعديل نوع الحساب.')
            else:
                t = ServiceType.objects.create(
                    name=name, icon=icon, color=color,
                    description=description, order=order, is_active=is_active,
                )
                if ajax:
                    return JsonResponse({'success': True, 'type': _service_type_payload(t)})
                messages.success(request, 'تم إضافة نوع الحساب.')
        if not ajax:
            return redirect('sysadmin:service_types')

    if ajax:
        return JsonResponse({'success': False, 'error': 'طلب غير صحيح'}, status=400)
    return render(request, 'sysadmin/service_type_form.html', {'obj': obj})


@superuser_required
def service_type_delete(request, pk):
    if request.method == 'POST':
        obj  = get_object_or_404(ServiceType, pk=pk)
        ajax = _is_ajax(request)
        if obj.centers.exists():
            err = 'لا يمكن حذف نوع مرتبط بحسابات موجودة.'
            if ajax:
                return JsonResponse({'success': False, 'error': err})
            messages.error(request, err)
        else:
            obj.delete()
            if ajax:
                return JsonResponse({'success': True})
            messages.success(request, 'تم حذف نوع الحساب.')
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


# ── Support Tickets ───────────────────────────────────────────────────────────

@superuser_required
def support_list(request):
    from apps.core.models import SupportTicket

    status_filter   = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_q        = request.GET.get('q', '').strip()

    tickets = SupportTicket.objects.select_related('center', 'created_by').order_by('-created_at')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if search_q:
        tickets = tickets.filter(
            Q(subject__icontains=search_q) | Q(center__name__icontains=search_q)
        )

    counts = {
        'all':         SupportTicket.objects.count(),
        'open':        SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'resolved':    SupportTicket.objects.filter(status='resolved').count(),
        'closed':      SupportTicket.objects.filter(status='closed').count(),
    }
    return render(request, 'sysadmin/support.html', {
        'tickets':         tickets,
        'counts':          counts,
        'status_filter':   status_filter,
        'priority_filter': priority_filter,
        'search_q':        search_q,
    })


@superuser_required
def support_detail(request, pk):
    from apps.core.models import SupportTicket, SupportMessage, Notification

    ticket          = get_object_or_404(SupportTicket.objects.select_related('center', 'created_by'), pk=pk)
    ticket_messages = ticket.messages.select_related('sender').order_by('created_at')

    if request.method == 'POST':
        body       = request.POST.get('body', '').strip()
        new_status = request.POST.get('status', ticket.status)

        if body:
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                sender_type='admin',
                body=body,
            )
            ticket.last_reply_at = timezone.now()
            ticket.assigned_to   = request.user
            Notification.objects.create(
                center=ticket.center,
                type='support_reply',
                title=f'رد جديد على تذكرتك #{ticket.pk}',
                body=f'فريق الدعم رد على التذكرة "{ticket.subject}". افتح التذكرة للاطلاع على الرد.',
                url=f'/support/{ticket.pk}/',
            )

        ticket.status = new_status
        if new_status == 'closed':
            ticket.closed_at = timezone.now()
        ticket.save()
        return redirect('sysadmin:support_detail', pk=pk)

    return render(request, 'sysadmin/support_detail.html', {
        'ticket':          ticket,
        'ticket_messages': ticket_messages,
    })
