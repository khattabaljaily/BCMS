from datetime import datetime, timedelta, date as date_type
from decimal import Decimal
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from apps.core.models import Center, Settings
from apps.services.models import Service
from apps.products.models import Product
from apps.billing.models import Invoice, InvoiceLine
from .models import OnlineBooking, StoreOrder, StoreOrderItem
from apps.appointments.models import Appointment, AppointmentService
from apps.clients.models import Client
from datetime import time as time_obj


# ── helpers ──────────────────────────────────────────────────────────────────

def _generate_slots(work_start, work_end, slot_minutes):
    """Return list of 'HH:MM' strings between work_start and work_end."""
    if not work_start or not work_end:
        return []
    slots = []
    current = datetime.combine(date_type.today(), work_start)
    end     = datetime.combine(date_type.today(), work_end)
    delta   = timedelta(minutes=slot_minutes or 30)
    while current < end:
        slots.append(current.strftime('%H:%M'))
        current += delta
    return slots


# ── Public store ──────────────────────────────────────────────────────────────

def store_home(request, slug):
    center       = get_object_or_404(Center, slug=slug, is_active=True)
    settings_obj, _ = Settings.objects.get_or_create(center=center)

    if not settings_obj.store_enabled and not settings_obj.booking_enabled:
        return render(request, 'store/disabled.html', {'center': center})

    services = Service.objects.filter(
        center=center, is_active=True, show_in_store=True
    ).select_related('category').order_by('category__name', 'name')

    products = Product.objects.filter(
        center=center, is_active=True, show_in_store=True, stock__gt=0
    ).order_by('name')

    today     = timezone.localdate()
    max_date  = today + timedelta(days=settings_obj.booking_advance_days or 30)
    time_slots = _generate_slots(
        settings_obj.work_start,
        settings_obj.work_end,
        settings_obj.slot_minutes,
    )

    work_days_list = settings_obj.work_days_list

    ctx = {
        'center':       center,
        'settings_obj': settings_obj,
        'services':     services,
        'products':     products,
        'today':        today.isoformat(),
        'max_date':     max_date.isoformat(),
        'time_slots':   json.dumps(time_slots),
        'work_days':    json.dumps(work_days_list),
        'currency':     center.currency,
    }

    # ── Handle booking POST ──────────────────────────────────
    if request.method == 'POST' and request.POST.get('_form') == 'booking':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        svc_id  = request.POST.get('service') or None
        bdate   = request.POST.get('date', '').strip()
        btime   = request.POST.get('time', '').strip() or None
        notes   = request.POST.get('notes', '').strip()

        # validate that chosen date is a work day
        date_ok = True
        if bdate and work_days_list:
            try:
                from datetime import date as date_cls
                chosen = date_cls.fromisoformat(bdate)
                # JS getDay() / our convention: 0=Sun...6=Sat
                chosen_day = chosen.isoweekday() % 7
                date_ok = chosen_day in work_days_list
            except ValueError:
                date_ok = False

        if name and phone and bdate and date_ok:
            OnlineBooking.objects.create(
                center=center,
                client_name=name,
                client_phone=phone,
                client_email=request.POST.get('email', '').strip(),
                service_id=svc_id,
                preferred_date=bdate,
                preferred_time=btime,
                notes=notes,
            )
            return render(request, 'store/success.html', {
                'center': center,
                'type': 'booking',
            })
        if not date_ok:
            ctx['booking_error'] = 'هذا اليوم ليس من أيام الدوام. يرجى اختيار يوم عمل.'
        else:
            ctx['booking_error'] = 'الاسم والهاتف والتاريخ مطلوبة.'
        ctx['active_tab'] = 'booking'

    # ── Handle order POST ────────────────────────────────────
    elif request.method == 'POST' and request.POST.get('_form') == 'order':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        notes   = request.POST.get('notes', '').strip()
        cart_json = request.POST.get('cart', '[]')

        try:
            cart = json.loads(cart_json)
        except (json.JSONDecodeError, ValueError):
            cart = []

        if name and phone and cart:
            order = StoreOrder.objects.create(
                center=center,
                client_name=name,
                client_phone=phone,
                client_address=address,
                notes=notes,
                total=Decimal('0'),
            )
            total = Decimal('0')
            for item in cart:
                try:
                    product = Product.objects.get(pk=item['id'], center=center, is_active=True)
                    qty     = max(1, int(item.get('qty', 1)))
                    price   = product.price
                    line    = StoreOrderItem(
                        order=order, product=product,
                        quantity=qty, unit_price=price,
                    )
                    line.save()
                    total += line.line_total
                except (Product.DoesNotExist, KeyError, ValueError):
                    pass
            order.total = total
            order.save(update_fields=['total'])

            return render(request, 'store/success.html', {
                'center': center,
                'type': 'order',
            })
        ctx['order_error'] = 'تأكد من إدخال اسمك وهاتفك واختيار منتج واحد على الأقل.'
        ctx['active_tab'] = 'products'

    return render(request, 'store/home.html', ctx)

def _convert_order_to_invoice(order):
    if order.status != 'pending':
        return None

    existing = Invoice.objects.filter(
        center=order.center,
        notes__startswith=f'طلب متجر #{order.pk}'
    ).first()
    if existing:
        return existing

    center = order.center
    client = None
    if order.client_phone:
        client = Client.objects.filter(center=center, phone=order.client_phone).first()

    settings_obj, _ = Settings.objects.get_or_create(center=center)
    number = settings_obj.next_invoice_number()
    invoice = Invoice.objects.create(
        center=center,
        number=number,
        client=client,
        payment_method='cash',
        status='draft',
        subtotal=order.total,
        discount_amount=Decimal('0'),
        tax_amount=Decimal('0'),
        total=order.total,
        paid_amount=Decimal('0'),
        notes=f'طلب متجر #{order.pk}',
    )

    for item in order.items.all():
        InvoiceLine.objects.create(
            invoice=invoice,
            description=item.product.name,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_percent=Decimal('0'),
        )

    return invoice


@login_required
def order_action(request, pk):
    order = get_object_or_404(StoreOrder, pk=pk, center=request.center)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm' and order.status == 'pending':
            invoice = _convert_order_to_invoice(order)
            if invoice:
                return redirect('billing:edit', pk=invoice.pk)
        elif action == 'cancel' and order.status == 'pending':
            order.status = 'cancelled'
            order.save(update_fields=['status'])
    return redirect('store:orders')

# ── Staff: manage online bookings ─────────────────────────────────────────────

@login_required
def bookings_list(request):
    center   = request.center
    status   = request.GET.get('status', 'new')
    bookings = OnlineBooking.objects.filter(center=center).select_related('service')
    if status:
        bookings = bookings.filter(status=status)
    return render(request, 'store/bookings.html', {
        'bookings':      bookings,
        'status_filter': status,
    })


def _convert_booking_to_appointment(booking):
    if booking.appointment:
        return booking.appointment

    center = booking.center
    client = None
    if booking.client_phone:
        client = Client.objects.filter(center=center, phone=booking.client_phone).first()

    appt_time = booking.preferred_time or time_obj(9, 0)
    appointment = Appointment.objects.create(
        center=center,
        client=client,
        date=booking.preferred_date,
        start_time=appt_time,
        walk_in_name=(booking.client_name if not client else ''),
        walk_in_phone=(booking.client_phone if not client else ''),
        notes=booking.notes,
        source='store',
        status='confirmed',
        total_price=0,
    )

    if booking.service:
        AppointmentService.objects.create(
            appointment=appointment,
            service=booking.service,
            unit_price=getattr(booking.service, 'price', 0)
        )

    try:
        appointment.recalculate_price()
    except Exception:
        pass

    booking.appointment = appointment
    booking.status = 'confirmed'
    booking.save(update_fields=['status', 'appointment'])
    return appointment


@login_required
def booking_action(request, pk):
    booking = get_object_or_404(OnlineBooking, pk=pk, center=request.center)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            _convert_booking_to_appointment(booking)
        elif action == 'cancel':
            booking.status = 'cancelled'
            booking.save(update_fields=['status'])
        elif action == 'convert':
            _convert_booking_to_appointment(booking)
    return redirect('store:bookings')


@login_required
def orders_list(request):
    center = request.center
    orders = StoreOrder.objects.filter(center=center).prefetch_related('items__product')
    return render(request, 'store/orders.html', {'orders': orders})
