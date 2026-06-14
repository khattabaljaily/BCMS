import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
from .models import Appointment, AppointmentService
from apps.services.models import Service
from apps.clients.models import Client
from apps.staff.models import Specialist


@login_required
def appointment_list(request):
    center = request.center
    date_str = request.GET.get('date')
    try:
        from datetime import date
        view_date = date.fromisoformat(date_str) if date_str else timezone.localdate()
    except ValueError:
        view_date = timezone.localdate()

    appointments = (
        Appointment.objects.filter(center=center, date=view_date)
        .select_related('client', 'specialist')
        .prefetch_related('appointment_services__service')
        .order_by('start_time')
    )
    specialists = Specialist.objects.filter(center=center, is_active=True)
    services    = Service.objects.filter(center=center, is_active=True).select_related('category')
    clients     = Client.objects.filter(center=center, is_active=True).order_by('name')[:200]

    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    return render(request, 'appointments/list.html', {
        'appointments': appointments,
        'specialists':  specialists,
        'services':     services,
        'clients':      clients,
        'view_date':    view_date,
        'prev_date':    prev_date,
        'next_date':    next_date,
        'today':        timezone.localdate(),
    })


@login_required
def appointment_save(request):
    center = request.center

    if request.method == 'GET':
        pk = request.GET.get('pk')
        obj = get_object_or_404(Appointment, pk=pk, center=center) if pk else None
        if obj and _is_ajax(request):
            return JsonResponse({
                'pk':           obj.pk,
                'client_id':    obj.client_id or '',
                'specialist_id': obj.specialist_id or '',
                'date':         str(obj.date),
                'start_time':   obj.start_time.strftime('%H:%M'),
                'end_time':     obj.end_time.strftime('%H:%M') if obj.end_time else '',
                'service_ids':  list(obj.appointment_services.values_list('service_id', flat=True)),
                'notes':        obj.notes,
                'status':       obj.status,
            })
        selected_ids = list(
            obj.appointment_services.values_list('service_id', flat=True)
        ) if obj else []
        return render(request, 'appointments/form.html', {
            'instance':            obj,
            'specialists':         Specialist.objects.filter(center=center, is_active=True),
            'services':            Service.objects.filter(center=center, is_active=True).select_related('category'),
            'clients':             Client.objects.filter(center=center, is_active=True).order_by('name')[:200],
            'selected_service_ids': selected_ids,
            'prefill_client_id':   request.GET.get('client', ''),
            'today':               timezone.localdate(),
        })

    pk  = request.POST.get('pk')
    obj = get_object_or_404(Appointment, pk=pk, center=center) if pk else Appointment(center=center)

    client_id = request.POST.get('client_id')
    obj.client        = Client.objects.filter(pk=client_id, center=center).first() if client_id else None
    obj.walk_in_name  = request.POST.get('walk_in_name', '').strip()
    obj.walk_in_phone = request.POST.get('walk_in_phone', '').strip()

    specialist_id  = request.POST.get('specialist_id')
    obj.specialist = Specialist.objects.filter(pk=specialist_id, center=center).first() if specialist_id else None

    obj.date       = request.POST.get('date')
    obj.start_time = request.POST.get('start_time')
    obj.end_time   = request.POST.get('end_time') or None
    obj.status     = request.POST.get('status', 'pending')
    obj.notes      = request.POST.get('notes', '').strip()
    obj.total_price = 0
    obj.save()

    AppointmentService.objects.filter(appointment=obj).delete()
    total = 0
    for sid in request.POST.getlist('service_ids'):
        svc = Service.objects.filter(pk=sid, center=center).first()
        if svc:
            AppointmentService.objects.create(appointment=obj, service=svc, unit_price=svc.price)
            total += svc.price
    obj.total_price = total
    obj.save(update_fields=['total_price'])

    if _is_ajax(request):
        return JsonResponse({'success': True, 'message': 'تم حفظ الموعد بنجاح.'})
    messages.success(request, 'تم الحفظ.')
    return redirect('appointments:list')


@login_required
def appointment_status(request, pk):
    obj = get_object_or_404(Appointment, pk=pk, center=request.center)
    if request.method == 'POST':
        new_status = request.POST.get('status', obj.status)
        obj.status = new_status
        obj.save(update_fields=['status'])
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم تحديث الحالة.'})
        messages.success(request, 'تم تحديث الحالة.')
    return redirect('appointments:list')


@login_required
def appointment_delete(request, pk):
    obj = get_object_or_404(Appointment, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف الموعد بنجاح.'})
        messages.success(request, 'تم الحذف.')
    return redirect('appointments:list')


@login_required
def calendar_view(request):
    center = request.center
    specialists = Specialist.objects.filter(center=center, is_active=True)
    services    = Service.objects.filter(center=center, is_active=True).select_related('category')
    clients     = Client.objects.filter(center=center, is_active=True).order_by('name')[:300]
    return render(request, 'appointments/calendar.html', {
        'specialists': specialists,
        'services':    services,
        'clients':     clients,
    })


@login_required
def calendar_events(request):
    center = request.center
    start  = request.GET.get('start', '')
    end    = request.GET.get('end', '')
    qs = Appointment.objects.filter(center=center).select_related('client', 'specialist')
    if start:
        qs = qs.filter(date__gte=start[:10])
    if end:
        qs = qs.filter(date__lte=end[:10])

    STATUS_COLORS = {
        'pending':     '#f59e0b',
        'confirmed':   '#6366f1',
        'in_progress': '#06b6d4',
        'completed':   '#10b981',
        'cancelled':   '#6b7280',
        'no_show':     '#ef4444',
    }

    events = []
    for a in qs:
        color = a.specialist.color if a.specialist else STATUS_COLORS.get(a.status, '#ec4899')
        events.append({
            'id':    a.pk,
            'title': a.client_display,
            'start': f'{a.date}T{a.start_time}',
            'end':   f'{a.date}T{a.end_time}' if a.end_time else None,
            'color': color,
            'extendedProps': {
                'status':     a.status,
                'specialist': a.specialist.name if a.specialist else '',
                'phone':      a.client_phone_display,
            },
        })
    return JsonResponse(events, safe=False)
