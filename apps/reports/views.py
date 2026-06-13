import json
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate, TruncMonth


@login_required
def reports_home(request):
    # Build context via helper
    context = _build_reports_context(request)
    return render(request, 'reports/home.html', context)


@login_required
def reports_print(request):
    """Render a print-friendly report page for exporting to PDF.

    Uses the same context as `reports_home` but a simplified template
    without navigation so users can print or save as PDF from the browser.
    """
    # Reuse the same data-building logic by calling reports_home's inner code
    # (we already prepared `context` above), so recompute by calling a helper
    # by duplicating the computation: simplest is to call reports_home logic
    # factor: move heavy logic into a helper here by repeating minimal code.
    # For maintainability, just call reports_home to compute context then
    # render the printable template with same context.
    # Construct context by reusing reports_home implementation
    context = _build_reports_context(request)
    return render(request, 'reports/print.html', context)


def _build_reports_context(request):
    center = request.center
    today  = timezone.localdate()

    # ── Date range ────────────────────────────────────────────
    period = request.GET.get('period', 'month')

    if period == 'month':
        date_from = today.replace(day=1)
        date_to   = today
    elif period == 'last_month':
        last_end  = today.replace(day=1) - timedelta(days=1)
        date_from = last_end.replace(day=1)
        date_to   = last_end
    elif period == 'year':
        date_from = today.replace(month=1, day=1)
        date_to   = today
    elif period == 'custom':
        try:
            date_from = date.fromisoformat(request.GET.get('from', ''))
            date_to   = date.fromisoformat(request.GET.get('to', ''))
        except (ValueError, TypeError):
            date_from = today.replace(day=1)
            date_to   = today
            period    = 'month'
    else:
        date_from = today.replace(day=1)
        date_to   = today

    from apps.billing.models      import Invoice, InvoiceLine
    from apps.appointments.models import Appointment, AppointmentService
    from apps.clients.models      import Client
    from apps.products.models     import Product
    from apps.finance.models      import Expense

    date_range = [date_from, date_to]
    num_days   = (date_to - date_from).days + 1
    # Use monthly grouping when range > 45 days
    use_monthly = num_days > 45

    # ── Revenue ──────────────────────────────────────────────
    paid_invoices = Invoice.objects.filter(center=center, date__range=date_range, status='paid')
    total_revenue = paid_invoices.aggregate(t=Sum('total'))['t'] or 0
    invoice_count = paid_invoices.count()

    prev_delta   = (date_to - date_from) + timedelta(days=1)
    prev_from    = date_from - prev_delta
    prev_to      = date_from - timedelta(days=1)
    prev_revenue = Invoice.objects.filter(
        center=center, date__range=[prev_from, prev_to], status='paid'
    ).aggregate(t=Sum('total'))['t'] or 0

    unpaid_total = Invoice.objects.filter(
        center=center, date__range=date_range
    ).exclude(status__in=['paid', 'cancelled']).aggregate(t=Sum('total'))['t'] or 0

    # Revenue chart (daily or monthly)
    if use_monthly:
        rev_rows = (
            paid_invoices
            .annotate(month=TruncMonth('date'))
            .values('month').annotate(total=Sum('total')).order_by('month')
        )
        rev_map = {r['month'].date(): float(r['total']) for r in rev_rows}
        chart_rev_labels, chart_rev_data = [], []
        cur = date_from.replace(day=1)
        end = date_to.replace(day=1)
        while cur <= end:
            chart_rev_labels.append(cur.strftime('%m/%Y'))
            chart_rev_data.append(rev_map.get(cur, 0))
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
    else:
        rev_rows = (
            paid_invoices.annotate(day=TruncDate('date'))
            .values('day').annotate(total=Sum('total')).order_by('day')
        )
        rev_map = {r['day']: float(r['total']) for r in rev_rows}
        chart_rev_labels, chart_rev_data = [], []
        for i in range(num_days):
            d = date_from + timedelta(days=i)
            chart_rev_labels.append(d.strftime('%d/%m'))
            chart_rev_data.append(rev_map.get(d, 0))

    # ── Payment method breakdown ──────────────────────────────
    METHOD_AR = {'cash': 'نقد', 'card_or_bank': 'بطاقة / بنك', 'later': 'آجل'}
    METHOD_CLR = {'cash': '#10b981', 'card_or_bank': '#3b82f6', 'later': '#f59e0b'}
    method_rows = (
        paid_invoices.values('payment_method')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('-total')
    )
    chart_method_labels, chart_method_data, chart_method_colors = [], [], []
    for row in method_rows:
        m = row['payment_method']
        if row['total']:
            chart_method_labels.append(METHOD_AR.get(m, m))
            chart_method_data.append(float(row['total']))
            chart_method_colors.append(METHOD_CLR.get(m, '#94a3b8'))

    # ── Expenses & Net Profit ─────────────────────────────────
    total_expenses = Expense.objects.filter(
        center=center, date__range=date_range
    ).aggregate(t=Sum('amount'))['t'] or 0
    net_profit = float(total_revenue) - float(total_expenses)

    # Expense breakdown by category
    expense_cats = (
        Expense.objects.filter(center=center, date__range=date_range)
        .values('category').annotate(total=Sum('amount')).order_by('-total')[:8]
    )

    # ── Appointments ─────────────────────────────────────────
    appointments    = Appointment.objects.filter(center=center, date__range=date_range)
    total_appts     = appointments.count()
    completed_appts = appointments.filter(status='completed').count()
    cancelled_appts = appointments.filter(status='cancelled').count()
    no_show_appts   = appointments.filter(status='no_show').count()

    STATUS_AR  = {
        'pending': 'قيد الانتظار', 'confirmed': 'مؤكد',
        'in_progress': 'جارٍ',     'completed': 'مكتمل',
        'cancelled': 'ملغي',        'no_show': 'لم يحضر',
    }
    STATUS_CLR = {
        'pending': '#f59e0b', 'confirmed': '#3b82f6',
        'in_progress': '#8b5cf6', 'completed': '#10b981',
        'cancelled': '#cbd5e1', 'no_show': '#ef4444',
    }
    status_rows = appointments.values('status').annotate(count=Count('id'))
    chart_status_labels, chart_status_data, chart_status_colors = [], [], []
    for row in status_rows:
        s = row['status']
        if row['count']:
            chart_status_labels.append(STATUS_AR.get(s, s))
            chart_status_data.append(row['count'])
            chart_status_colors.append(STATUS_CLR.get(s, '#94a3b8'))

    if use_monthly:
        appt_rows = (
            appointments.annotate(month=TruncMonth('date'))
            .values('month').annotate(count=Count('id')).order_by('month')
        )
        appt_map = {r['month'].date(): r['count'] for r in appt_rows}
        chart_appt_labels, chart_appt_data = [], []
        cur = date_from.replace(day=1)
        end = date_to.replace(day=1)
        while cur <= end:
            chart_appt_labels.append(cur.strftime('%m/%Y'))
            chart_appt_data.append(appt_map.get(cur, 0))
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
    else:
        appt_rows = (
            appointments.annotate(day=TruncDate('date'))
            .values('day').annotate(count=Count('id')).order_by('day')
        )
        appt_map = {r['day']: r['count'] for r in appt_rows}
        chart_appt_labels, chart_appt_data = [], []
        for i in range(num_days):
            d = date_from + timedelta(days=i)
            chart_appt_labels.append(d.strftime('%d/%m'))
            chart_appt_data.append(appt_map.get(d, 0))

    # ── Top Services ─────────────────────────────────────────
    top_services = (
        AppointmentService.objects
        .filter(appointment__center=center, appointment__date__range=date_range)
        .values('service__name')
        .annotate(count=Count('id'), revenue=Sum('unit_price'))
        .order_by('-count')[:10]
    )

    # ── Top Products (via invoice lines) ─────────────────────
    top_products = (
        InvoiceLine.objects
        .filter(
            invoice__center=center,
            invoice__date__range=date_range,
            invoice__status='paid',
            product__isnull=False,
        )
        .values('product__name')
        .annotate(qty=Sum('quantity'), revenue=Sum('line_total'))
        .order_by('-revenue')[:10]
    )

    # ── Staff Performance ────────────────────────────────────
    staff_perf = (
        Appointment.objects
        .filter(center=center, date__range=date_range, specialist__isnull=False)
        .values('specialist__name', 'specialist__color')
        .annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            revenue=Sum('total_price'),
        )
        .order_by('-completed')
    )

    # ── Top Clients ──────────────────────────────────────────
    top_clients = (
        Client.objects.filter(center=center)
        .annotate(
            period_paid=Sum(
                'invoices__total',
                filter=Q(invoices__status='paid', invoices__date__range=date_range)
            ),
            period_appts=Count(
                'appointments',
                filter=Q(appointments__date__range=date_range)
            ),
        )
        .filter(period_paid__gt=0)
        .order_by('-period_paid')[:10]
    )

    new_clients_count = Client.objects.filter(
        center=center, created_at__date__range=date_range,
    ).count()

    # ── Low Stock ────────────────────────────────────────────
    low_stock = Product.objects.filter(
        center=center, is_active=True, stock__lte=5
    ).order_by('stock')[:10]

    context = {
        'period':    period,
        'date_from': date_from,
        'date_to':   date_to,
        'today':     today,

        'total_revenue':  total_revenue,
        'prev_revenue':   prev_revenue,
        'invoice_count':  invoice_count,
        'unpaid_total':   unpaid_total,
        'chart_rev_labels': json.dumps(chart_rev_labels),
        'chart_rev_data':   json.dumps(chart_rev_data),

        'chart_method_labels': json.dumps(chart_method_labels),
        'chart_method_data':   json.dumps(chart_method_data),
        'chart_method_colors': json.dumps(chart_method_colors),

        'total_expenses': total_expenses,
        'net_profit':     net_profit,
        'expense_cats':   expense_cats,

        'total_appts':     total_appts,
        'completed_appts': completed_appts,
        'cancelled_appts': cancelled_appts,
        'no_show_appts':   no_show_appts,
        'chart_status_labels': json.dumps(chart_status_labels),
        'chart_status_data':   json.dumps(chart_status_data),
        'chart_status_colors': json.dumps(chart_status_colors),
        'chart_appt_labels':   json.dumps(chart_appt_labels),
        'chart_appt_data':     json.dumps(chart_appt_data),

        'top_services':      top_services,
        'top_products':      top_products,
        'staff_perf':        staff_perf,
        'top_clients':       top_clients,
        'new_clients_count': new_clients_count,
        'low_stock':         low_stock,
    }

    return context
