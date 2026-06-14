import json
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.views.decorators.cache import cache_control


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@cache_control(max_age=86400)
def service_worker(request):
    sw = """
const CACHE = 'bcms-v1';
const OFFLINE = ['/dashboard/', '/'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(OFFLINE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.url.includes('/admin/')) return;
  e.respondWith(
    fetch(e.request)
      .then(r => {
        const clone = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return r;
      })
      .catch(() => caches.match(e.request).then(r => r || caches.match('/dashboard/')))
  );
});
"""
    return HttpResponse(sw.strip(), content_type='application/javascript')


def manifest(request):
    center_name = 'EnjazBCMS'
    try:
        if hasattr(request, 'center') and request.center:
            center_name = request.center.name
    except Exception:
        pass
    data = {
        'name': center_name,
        'short_name': 'BCMS',
        'description': 'نظام إدارة مراكز التجميل',
        'start_url': '/dashboard/',
        'display': 'standalone',
        'orientation': 'portrait',
        'background_color': '#ffffff',
        'theme_color': '#db2777',
        'lang': 'ar',
        'dir': 'rtl',
        'icons': [
            {'src': '/static/img/logo/logo-ffffff.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/static/img/logo/logo-ffffff.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
        ],
        'categories': ['business', 'productivity'],
    }
    return HttpResponse(json.dumps(data, ensure_ascii=False), content_type='application/manifest+json')


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('sysadmin:dashboard')
    center = request.center
    today  = timezone.localdate()

    from apps.appointments.models import Appointment
    from apps.billing.models      import Invoice
    from apps.clients.models      import Client

    # ── Today's appointments ─────────────────────────────────
    today_appointments = (
        Appointment.objects
        .filter(center=center, date=today)
        .select_related('client', 'specialist')
        .order_by('start_time')
    )

    # ── Quick stats ──────────────────────────────────────────
    prev_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    prev_month_end   = today.replace(day=1) - timedelta(days=1)

    from apps.finance.models import ClientPayment as _CP

    def _month_revenue(year, month=None, date_gte=None, date_lte=None):
        """Sum billing-immediate paid invoices + finance client payments for a period."""
        if month is not None:
            inv_qs = Invoice.objects.filter(
                center=center, date__year=year, date__month=month,
                status='paid', payment_method__in=['cash', 'card_or_bank']
            )
            pay_qs = _CP.objects.filter(
                center=center, date__year=year, date__month=month,
                status='confirmed'
            )
        else:
            inv_qs = Invoice.objects.filter(
                center=center, date__gte=date_gte, date__lte=date_lte,
                status='paid', payment_method__in=['cash', 'card_or_bank']
            )
            pay_qs = _CP.objects.filter(
                center=center, date__gte=date_gte, date__lte=date_lte,
                status='confirmed'
            )
        return (
            (inv_qs.aggregate(t=Sum('paid_amount'))['t'] or 0) +
            (pay_qs.aggregate(t=Sum('amount'))['t'] or 0)
        )

    month_revenue = _month_revenue(today.year, month=today.month)
    prev_revenue  = _month_revenue(
        prev_month_start.year,
        date_gte=prev_month_start,
        date_lte=prev_month_end,
    )

    total_clients = Client.objects.filter(center=center).count()
    new_clients   = Client.objects.filter(
        center=center,
        created_at__year=today.year,
        created_at__month=today.month,
    ).count()

    month_appts = Appointment.objects.filter(
        center=center, date__year=today.year, date__month=today.month
    ).count()

    stats = {
        'today_count':     today_appointments.count(),
        'today_confirmed': today_appointments.filter(status='confirmed').count(),
        'total_clients':   total_clients,
        'new_clients':     new_clients,
        'month_revenue':   month_revenue,
        'prev_revenue':    prev_revenue,
        'month_appts':     month_appts,
        'pending_bookings': 0,
    }

    try:
        from apps.store.models import OnlineBooking
        stats['pending_bookings'] = OnlineBooking.objects.filter(
            center=center, status='new'
        ).count()
    except Exception:
        pass

    # ── Upcoming (7 days) ────────────────────────────────────
    upcoming = (
        Appointment.objects
        .filter(
            center=center,
            date__gte=today,
            date__lte=today + timedelta(days=7),
            status__in=['pending', 'confirmed'],
        )
        .select_related('client', 'specialist')
        .order_by('date', 'start_time')[:8]
    )

    # ── Extra widgets: today's revenue, unpaid invoices, low-stock products, recent clients
    today_rev_billing = Invoice.objects.filter(
        center=center, date=today, status='paid',
        payment_method__in=['cash', 'card_or_bank']
    ).aggregate(t=Sum('paid_amount'))['t'] or 0
    today_rev_finance = _CP.objects.filter(
        center=center, date=today, status='confirmed'
    ).aggregate(t=Sum('amount'))['t'] or 0
    today_revenue = today_rev_billing + today_rev_finance

    unpaid_qs = Invoice.objects.filter(center=center).exclude(status='paid').exclude(status='cancelled')
    unpaid_count = unpaid_qs.count()
    unpaid_total = unpaid_qs.aggregate(t=Sum('total'))['t'] or 0

    low_stock_products = []
    try:
        from apps.products.models import Product
        low_stock_products = list(Product.objects.filter(center=center, stock__lte=5).order_by('stock')[:6])
    except Exception:
        low_stock_products = []

    recent_clients = list(Client.objects.filter(center=center).order_by('-created_at')[:6])

    # ── Expenses stats ───────────────────────────────────────
    from apps.finance.models import Expense
    today_expenses = Expense.objects.filter(
        center=center, date=today
    ).aggregate(t=Sum('amount'))['t'] or 0
    month_expenses = Expense.objects.filter(
        center=center, date__year=today.year, date__month=today.month
    ).aggregate(t=Sum('amount'))['t'] or 0
    month_net = (month_revenue or 0) - month_expenses

    # ── Chart: revenue + expenses last 30 days ──────────────
    thirty_ago = today - timedelta(days=29)
    rev_rows = (
        Invoice.objects
        .filter(center=center, date__gte=thirty_ago, status='paid',
                payment_method__in=['cash', 'card_or_bank'])
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('paid_amount'))
        .order_by('day')
    )
    rev_map = {r['day']: float(r['total']) for r in rev_rows}
    pay_rows = (
        _CP.objects
        .filter(center=center, date__gte=thirty_ago, status='confirmed')
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    for r in pay_rows:
        rev_map[r['day']] = rev_map.get(r['day'], 0) + float(r['total'])

    exp_rows = (
        Expense.objects
        .filter(center=center, date__gte=thirty_ago)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    exp_map = {r['day']: float(r['total']) for r in exp_rows}

    chart_rev_labels, chart_rev_data, chart_exp_data = [], [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        chart_rev_labels.append(d.strftime('%d/%m'))
        chart_rev_data.append(rev_map.get(d, 0))
        chart_exp_data.append(exp_map.get(d, 0))
    rev_30_total = sum(chart_rev_data)

    # ── Chart: appointments last 14 days ─────────────────────
    fourteen_ago = today - timedelta(days=13)
    appt_rows = (
        Appointment.objects
        .filter(center=center, date__gte=fourteen_ago, date__lte=today)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    appt_map = {r['day']: r['count'] for r in appt_rows}
    chart_appt_labels, chart_appt_data = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        chart_appt_labels.append(d.strftime('%d/%m'))
        chart_appt_data.append(appt_map.get(d, 0))

    # ── Chart: appointment status this month ─────────────────
    STATUS_AR = {
        'pending':     'قيد الانتظار',
        'confirmed':   'مؤكد',
        'in_progress': 'جارٍ',
        'completed':   'مكتمل',
        'cancelled':   'ملغي',
    }
    STATUS_CLR = {
        'pending':     '#f59e0b',
        'confirmed':   '#3b82f6',
        'in_progress': '#8b5cf6',
        'completed':   '#10b981',
        'cancelled':   '#cbd5e1',
    }
    status_rows = (
        Appointment.objects
        .filter(center=center, date__year=today.year, date__month=today.month)
        .values('status')
        .annotate(count=Count('id'))
    )
    chart_status_labels, chart_status_data, chart_status_colors = [], [], []
    for row in status_rows:
        s = row['status']
        chart_status_labels.append(STATUS_AR.get(s, s))
        chart_status_data.append(row['count'])
        chart_status_colors.append(STATUS_CLR.get(s, '#94a3b8'))

    return render(request, 'core/dashboard.html', {
        'today_appointments': today_appointments,
        'upcoming':           upcoming,
        'stats':              stats,
        'today':              today,
        'today_revenue':      today_revenue,
        'unpaid_count':       unpaid_count,
        'unpaid_total':       unpaid_total,
        'low_stock_products': low_stock_products,
        'recent_clients':     recent_clients,
        # chart data (JSON-safe)
        'today_expenses':        today_expenses,
        'month_expenses':        month_expenses,
        'month_net':             month_net,
        'chart_rev_labels':      json.dumps(chart_rev_labels),
        'chart_rev_data':        json.dumps(chart_rev_data),
        'chart_exp_data':        json.dumps(chart_exp_data),
        'rev_30_total':          rev_30_total,
        'chart_appt_labels':     json.dumps(chart_appt_labels),
        'chart_appt_data':       json.dumps(chart_appt_data),
        'chart_status_labels':   json.dumps(chart_status_labels),
        'chart_status_data':     json.dumps(chart_status_data),
        'chart_status_colors':   json.dumps(chart_status_colors),
    })


@login_required
def settings(request):
    """Settings page for center configuration"""
    from .models import Settings
    
    center = request.center
    settings_obj, _ = Settings.objects.get_or_create(center=center)
    
    if request.method == 'POST':
        # Update center data
        center.phone   = request.POST.get('phone', '').strip()
        center.email   = request.POST.get('email', '').strip()
        center.address = request.POST.get('address', '').strip()
        center.city    = request.POST.get('city', '').strip()
        # Handle logo removal or update
        if request.POST.get('remove_logo'):
            try:
                if center.logo:
                    center.logo.delete(save=False)
            except Exception:
                pass
            center.logo = None

        if 'logo' in request.FILES:
            center.logo = request.FILES['logo']
        center.save()
        
        # Update settings data
        settings_obj.invoice_prefix      = request.POST.get('invoice_prefix', 'INV')
        settings_obj.invoice_footer      = request.POST.get('invoice_footer', '')
        settings_obj.show_tax_on_invoice = bool(request.POST.get('show_tax_on_invoice'))
        settings_obj.tax_percent         = request.POST.get('tax_percent', 0) or 0
        settings_obj.booking_enabled     = bool(request.POST.get('booking_enabled'))
        settings_obj.booking_advance_days = int(request.POST.get('booking_advance_days', 30) or 30)
        settings_obj.slot_minutes        = int(request.POST.get('slot_minutes', 30) or 30)
        settings_obj.work_start          = request.POST.get('work_start') or None
        settings_obj.work_end            = request.POST.get('work_end') or None
        work_days_raw = request.POST.getlist('work_days')
        settings_obj.work_days           = ','.join(work_days_raw) if work_days_raw else ''
        settings_obj.store_enabled       = bool(request.POST.get('store_enabled'))
        settings_obj.store_name          = request.POST.get('store_name', '')
        # Handle store cover removal or update
        if request.POST.get('remove_store_cover'):
            try:
                if settings_obj.store_cover:
                    settings_obj.store_cover.delete(save=False)
            except Exception:
                pass
            settings_obj.store_cover = None

        if 'store_cover' in request.FILES:
            settings_obj.store_cover = request.FILES['store_cover']
        settings_obj.loyalty_enabled     = bool(request.POST.get('loyalty_enabled'))
        settings_obj.points_per_currency = int(request.POST.get('points_per_currency', 1) or 1)
        settings_obj.reminder_enabled    = bool(request.POST.get('reminder_enabled'))
        settings_obj.reminder_hours_before = int(request.POST.get('reminder_hours_before', 24) or 24)
        settings_obj.save()

        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حفظ الإعدادات بنجاح.'})
        messages.success(request, 'تم حفظ الإعدادات بنجاح.')
        return render(request, 'core/settings.html', {
            'center': center,
            'settings_obj': settings_obj,
        })
    
    return render(request, 'core/settings.html', {
        'center': center,
        'settings_obj': settings_obj,
    })
