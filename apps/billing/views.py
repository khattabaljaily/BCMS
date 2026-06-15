import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.db import transaction
from decimal import Decimal
from .models import Invoice, InvoiceLine
from apps.clients.models import Client
from apps.services.models import Service
from apps.products.models import Product, StockMovement


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _billing_ref(pk):
    return f'billing_{pk}'


def _payment_ref(pk):
    return f'payment_{pk}'


def _create_invoice_treasury_movement(invoice):
    """Record a paid cash/card invoice as a treasury inflow. No-op for 'later' or if already recorded."""
    if invoice.payment_method not in ('cash', 'card_or_bank'):
        return
    from apps.finance.models import Treasury, TreasuryMovement
    treasury = Treasury.objects.filter(center=invoice.center).first()
    if not treasury:
        return
    ref = _billing_ref(invoice.pk)
    if TreasuryMovement.objects.filter(treasury__center=invoice.center, reference=ref).exists():
        return
    TreasuryMovement.objects.create(
        treasury=treasury,
        type='in',
        amount=invoice.paid_amount,
        reference=ref,
        notes=f'فاتورة {invoice.number}',
    )


def _delete_invoice_treasury_movement(invoice):
    """Remove treasury movement recorded for this invoice's direct payment."""
    from apps.finance.models import TreasuryMovement
    for tm in TreasuryMovement.objects.filter(
        treasury__center=invoice.center,
        reference=_billing_ref(invoice.pk),
    ):
        tm.delete()


def _reverse_invoice_treasury_movement(invoice):
    """Create reversal treasury movement for a voided invoice (audit trail)."""
    from apps.finance.models import TreasuryMovement
    for tm in TreasuryMovement.objects.filter(
        treasury__center=invoice.center,
        reference=_billing_ref(invoice.pk),
    ):
        opposite = 'out' if tm.type == 'in' else 'in'
        TreasuryMovement.objects.create(
            treasury=tm.treasury,
            type=opposite,
            amount=tm.amount,
            reference=f'rev_{tm.reference}',
            notes=f'إلغاء فاتورة {invoice.number}',
        )


def _cancel_invoice_client_payments(invoice):
    """
    Cancel all confirmed client payments and REMOVE treasury movements.
    Used when permanently deleting an invoice.
    """
    from apps.finance.models import TreasuryMovement
    for payment in invoice.payments.filter(status='confirmed'):
        for tm in TreasuryMovement.objects.filter(
            treasury__center=invoice.center,
            reference=_payment_ref(payment.pk),
        ):
            tm.delete()
        payment.status = 'cancelled'
        payment.save(update_fields=['status'])


def _void_invoice_client_payments(invoice):
    """
    Cancel all confirmed client payments and CREATE reversal treasury movements.
    Used when voiding an invoice so the audit trail is preserved.
    """
    from apps.finance.models import TreasuryMovement
    for payment in invoice.payments.filter(status='confirmed'):
        for tm in TreasuryMovement.objects.filter(
            treasury__center=invoice.center,
            reference=_payment_ref(payment.pk),
        ):
            opposite = 'out' if tm.type == 'in' else 'in'
            TreasuryMovement.objects.create(
                treasury=tm.treasury,
                type=opposite,
                amount=tm.amount,
                reference=f'rev_{tm.reference}',
                notes=f'إلغاء دفعة فاتورة {invoice.number}',
            )
        payment.status = 'cancelled'
        payment.save(update_fields=['status'])


def get_invoice_lines_from_post(request, center):
    descs = request.POST.getlist('description[]') or request.POST.getlist('description')
    qtys = request.POST.getlist('quantity[]') or request.POST.getlist('quantity')
    prices = request.POST.getlist('unit_price[]') or request.POST.getlist('unit_price')
    discs = request.POST.getlist('discount_percent[]') or request.POST.getlist('discount_percent')
    product_ids = request.POST.getlist('product_id[]') or request.POST.getlist('product_id')
    service_ids = request.POST.getlist('service_id[]') or request.POST.getlist('service_id')

    lines = []
    for i, desc in enumerate(descs):
        if not desc.strip():
            continue
        qty = Decimal(qtys[i] if i < len(qtys) and qtys[i] else '1')
        price = Decimal(prices[i] if i < len(prices) and prices[i] else '0')
        discount = Decimal(discs[i] if i < len(discs) and discs[i] else '0')
        service_id = service_ids[i] if i < len(service_ids) else None
        product_id = product_ids[i] if i < len(product_ids) else None
        service = Service.objects.filter(pk=service_id, center=center).first() if service_id else None
        product = Product.objects.filter(pk=product_id, center=center).first() if product_id else None

        lines.append({
            'description': desc,
            'quantity': qty,
            'unit_price': price,
            'discount_percent': discount,
            'service': service,
            'product': product,
        })
    return lines


def _parse_store_order_id_from_notes(notes):
    if not notes:
        return None
    match = re.search(r'طلب متجر #(\d+)', notes)
    return int(match.group(1)) if match else None


@login_required
def invoice_list(request):
    center = request.center
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    invoices = Invoice.objects.filter(center=center).select_related('client')
    if q:
        invoices = invoices.filter(
            Q(number__icontains=q) | Q(client__name__icontains=q)
        )
    if status:
        invoices = invoices.filter(status=status)
    return render(request, 'billing/list.html', {
        'invoices': invoices,
        'q': q,
        'status_filter': status,
        'status_choices': Invoice.STATUS,
    })


@login_required
@transaction.atomic
def invoice_create(request):
    center = request.center

    clients = (
        Client.objects.filter(center=center, is_active=True)
        .annotate(
            visit_ct=Count('appointments', filter=Q(appointments__status='completed')),
            spent_sum=Sum('invoices__total', filter=Q(invoices__status='paid')),
        )
        .order_by('name')
    )
    services = Service.objects.filter(center=center, is_active=True).select_related('category')
    products = Product.objects.filter(center=center, is_active=True)

    prefill_client_id = None
    prefill_appointment_id = None
    appointment_param = request.GET.get('appointment') or request.POST.get('appointment')
    if appointment_param:
        from apps.appointments.models import Appointment
        appointment = Appointment.objects.filter(pk=appointment_param, center=center).select_related('client').first()
        if appointment:
            prefill_appointment_id = appointment.pk
            if appointment.client_id:
                prefill_client_id = appointment.client_id

    if request.method == 'POST':
        from apps.core.models import Settings
        settings_obj, _ = Settings.objects.get_or_create(center=center)
        number = settings_obj.next_invoice_number()

        client_id = request.POST.get('client')
        appointment_id = request.POST.get('appointment')
        lines = get_invoice_lines_from_post(request, center)
        if not lines:
            messages.error(request, 'يجب إضافة بند واحد على الأقل للفاتورة.')
        else:
            payment_method = request.POST.get('payment_method', 'cash')
            inv = Invoice.objects.create(
                center=center,
                number=number,
                client_id=client_id or None,
                appointment_id=appointment_id or None,
                payment_method=payment_method,
                notes=request.POST.get('notes', ''),
                discount_amount=Decimal(request.POST.get('discount_amount') or '0'),
                status='draft',
            )

            for item in lines:
                InvoiceLine.objects.create(
                    invoice=inv,
                    description=item['description'],
                    service=item['service'],
                    product=item['product'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    discount_percent=item['discount_percent'],
                )

                if item['product']:
                    StockMovement.objects.create(
                        center=center,
                        product=item['product'],
                        change=-item['quantity'],
                        type='sale',
                        reference=f'invoice_{inv.pk}',
                        notes=f'Invoice #{inv.number}',
                    )

            inv.recalculate()

            action = request.POST.get('action')
            if action == 'pay':
                if payment_method == 'later':
                    # Pay-later: save as draft, no treasury movement
                    inv.status = 'draft'
                    inv.paid_amount = Decimal('0')
                    inv.save(update_fields=['status', 'paid_amount'])
                else:
                    inv.mark_paid(amount=inv.total, method=payment_method)
                    _create_invoice_treasury_movement(inv)
            else:
                # draft — save without payment
                inv.status = 'draft'
                inv.paid_amount = Decimal('0')
                inv.save(update_fields=['status', 'paid_amount'])

            return redirect('billing:detail', pk=inv.pk)
        

    clients_json = json.dumps([{
        'id':     c.pk,
        'name':   c.name,
        'phone':  str(c.phone or ''),
        'email':  c.email,
        'visits': c.visit_ct or 0,
        'spent':  float(c.spent_sum or 0),
    } for c in clients])

    services_json = json.dumps([{
        'id':       s.pk,
        'name':     s.name,
        'price':    float(s.price),
        'category': s.category.name if s.category else '',
        'duration': s.duration_display,
    } for s in services])

    products_json = json.dumps([{
        'id':    p.pk,
        'name':  p.name,
        'price': float(p.price),
        'sku':   p.sku or '',
    } for p in products])

    return render(request, 'billing/form.html', {
        'clients_json':  clients_json,
        'services_json': services_json,
        'products_json': products_json,
        'today':         timezone.localdate().isoformat(),
        'payment_choices': Invoice.PAYMENT,
        'prefill_client_id': prefill_client_id,
        'prefill_appointment_id': prefill_appointment_id,
        'edit_mode': False,
    })


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, center=request.center)
    lines = inv.lines.select_related('service', 'product')
    return render(request, 'billing/detail.html', {
        'inv': inv,
        'lines': lines,
    })


@login_required
def invoice_print(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, center=request.center)
    lines = inv.lines.select_related('service', 'product')
    from apps.core.models import Settings
    settings_obj, _ = Settings.objects.get_or_create(center=request.center)
    return render(request, 'billing/print.html', {
        'inv': inv,
        'lines': lines,
        'settings_obj': settings_obj,
    })


@login_required
@transaction.atomic
def invoice_void(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, center=request.center)
    if request.method == 'POST':
        # 1. Cancel client payments + create reversal treasury movements (audit trail)
        _void_invoice_client_payments(inv)

        # 2. Create reversal for invoice's own direct treasury movement
        _reverse_invoice_treasury_movement(inv)

        # 3. Reverse stock: create reversal movements instead of deleting
        for sm in StockMovement.objects.filter(reference=f'invoice_{inv.pk}'):
            StockMovement.objects.create(
                center=sm.center,
                product=sm.product,
                change=-sm.change,
                type='reversal',
                reference=f'rev_{sm.reference}',
                notes=f'إلغاء فاتورة {inv.number}',
            )

        # 4. Mark cancelled and zero out paid amount
        inv.status = 'cancelled'
        inv.paid_amount = Decimal('0')
        inv.save(update_fields=['status', 'paid_amount'])

        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم إلغاء الفاتورة واستعادة المخزون والخزينة.'})
        messages.success(request, 'تم إلغاء الفاتورة واستعادة المخزون والخزينة.')
    return redirect('billing:list')


@login_required
@transaction.atomic
def invoice_edit(request, pk):
    center = request.center
    inv = get_object_or_404(Invoice, pk=pk, center=center)

    clients = (
        Client.objects.filter(center=center, is_active=True)
        .annotate(
            visit_ct=Count('appointments', filter=Q(appointments__status='completed')),
            spent_sum=Sum('invoices__total', filter=Q(invoices__status='paid')),
        )
        .order_by('name')
    )
    services = Service.objects.filter(center=center, is_active=True).select_related('category')
    products = Product.objects.filter(center=center, is_active=True)

    store_order_id = _parse_store_order_id_from_notes(inv.notes)
    store_order = None
    if store_order_id:
        from apps.store.models import StoreOrder
        store_order = StoreOrder.objects.filter(pk=store_order_id, center=center, status='pending').first()

    if request.method == 'POST':
        lines = get_invoice_lines_from_post(request, center)
        if not lines:
            messages.error(request, 'يجب إضافة بند واحد على الأقل للفاتورة.')
        else:
            prev_method = inv.payment_method
            prev_status = inv.status

            # Restore old stock movements
            for movement in StockMovement.objects.filter(reference=f'invoice_{inv.pk}'):
                movement.delete()

            # Update invoice header
            payment_method = request.POST.get('payment_method', 'cash')
            inv.client_id      = request.POST.get('client') or None
            inv.payment_method = payment_method
            inv.notes          = request.POST.get('notes', '')
            inv.discount_amount = Decimal(request.POST.get('discount_amount') or '0')
            inv.save(update_fields=['client_id', 'payment_method', 'notes', 'discount_amount'])

            # Rebuild lines
            inv.lines.all().delete()
            for item in lines:
                InvoiceLine.objects.create(
                    invoice=inv,
                    description=item['description'],
                    service=item['service'],
                    product=item['product'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    discount_percent=item['discount_percent'],
                )
                if item['product']:
                    StockMovement.objects.create(
                        center=center,
                        product=item['product'],
                        change=-item['quantity'],
                        type='sale',
                        reference=f'invoice_{inv.pk}',
                        notes=f'Invoice #{inv.number}',
                    )

            inv.recalculate()

            action = request.POST.get('action')
            if action == 'pay':
                if payment_method == 'later':
                    # Switching to pay-later: remove direct treasury movement, cancel prior client payments
                    _delete_invoice_treasury_movement(inv)
                    inv.status = 'draft'
                    inv.paid_amount = Decimal('0')
                    inv.save(update_fields=['status', 'paid_amount'])
                else:
                    # Pay now (cash/card): replace treasury movement with updated amount
                    _delete_invoice_treasury_movement(inv)
                    inv.mark_paid(amount=inv.total, method=payment_method)
                    _create_invoice_treasury_movement(inv)
            else:
                # Draft save — reconcile treasury if already paid
                if prev_status == 'paid' and payment_method in ('cash', 'card_or_bank'):
                    # Total may have changed: replace movement with new amount
                    _delete_invoice_treasury_movement(inv)
                    inv.mark_paid(amount=inv.total, method=payment_method)
                    _create_invoice_treasury_movement(inv)
                elif prev_status == 'paid' and payment_method == 'later':
                    # Switched from paid to later: remove treasury, clear payment
                    _delete_invoice_treasury_movement(inv)
                    inv.status = 'draft'
                    inv.paid_amount = Decimal('0')
                    inv.save(update_fields=['status', 'paid_amount'])
                elif prev_method in ('cash', 'card_or_bank') and payment_method == 'later':
                    # Payment method changed to later without explicit action
                    _delete_invoice_treasury_movement(inv)

            if store_order and store_order.status == 'pending':
                store_order.status = 'confirmed'
                store_order.save(update_fields=['status'])

            messages.success(request, 'تم التحديث.')
            return redirect('billing:detail', pk=inv.pk)

    clients_json = json.dumps([{
        'id':     c.pk,
        'name':   c.name,
        'phone':  str(c.phone or ''),
        'email':  c.email,
        'visits': c.visit_ct or 0,
        'spent':  float(c.spent_sum or 0),
    } for c in clients])

    services_json = json.dumps([{
        'id':       s.pk,
        'name':     s.name,
        'price':    float(s.price),
        'category': s.category.name if s.category else '',
        'duration': s.duration_display,
    } for s in services])

    products_json = json.dumps([{
        'id':    p.pk,
        'name':  p.name,
        'price': float(p.price),
        'sku':   p.sku or '',
    } for p in products])

    return render(request, 'billing/form.html', {
        'inv': inv,
        'edit_mode': True,
        'clients_json':  clients_json,
        'services_json': services_json,
        'products_json': products_json,
        'today':         timezone.localdate().isoformat(),
        'payment_choices': Invoice.PAYMENT,
        'store_order_id': store_order_id,
    })


@login_required
@transaction.atomic
def invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk, center=request.center)

    if request.method == 'POST':
        # Cancel client payments + remove their treasury movements BEFORE cascade delete
        _cancel_invoice_client_payments(inv)

        # Remove direct invoice treasury movement
        _delete_invoice_treasury_movement(inv)

        # Restore stock
        StockMovement.objects.filter(reference=f'invoice_{inv.pk}').delete()

        # Delete invoice (cascades to lines and payments)
        inv.delete()

        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف الفاتورة واستعادة المخزون والخزينة.'})
        messages.success(request, 'تم حذف الفاتورة واستعادة المخزون والخزينة.')
        return redirect('billing:list')

    return redirect('billing:detail', pk=pk)


# ══════════════════════════════════════════════════════════════
# POS — نقطة البيع
# ══════════════════════════════════════════════════════════════

@login_required
def pos_view(request):
    center = request.center
    from apps.services.models import ServiceCategory

    clients = (
        Client.objects.filter(center=center, is_active=True)
        .order_by('name')
        .values('id', 'name', 'phone')
    )
    categories = ServiceCategory.objects.filter(center=center, is_active=True).prefetch_related(
        'services'
    ).order_by('order', 'name')
    services = Service.objects.filter(center=center, is_active=True).select_related('category').order_by('category__order', 'order', 'name')
    products = Product.objects.filter(center=center, is_active=True).order_by('name')

    clients_json = json.dumps(list(clients))
    services_json = json.dumps([{
        'id': s.pk, 'name': s.name,
        'price': float(s.price),
        'category_id': s.category_id,
        'category': s.category.name if s.category else 'عام',
    } for s in services])
    products_json = json.dumps([{
        'id': p.pk, 'name': p.name,
        'price': float(p.price),
        'stock': float(p.stock),
        'sku': p.sku,
    } for p in products])
    categories_json = json.dumps([{
        'id': c.pk, 'name': c.name, 'icon': c.icon, 'color': c.color,
    } for c in categories])

    return render(request, 'billing/pos.html', {
        'clients_json':    clients_json,
        'services_json':   services_json,
        'products_json':   products_json,
        'categories_json': categories_json,
        'payment_choices': Invoice.PAYMENT,
    })


@login_required
@transaction.atomic
def pos_save(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'بيانات غير صحيحة'}, status=400)

    center = request.center
    items = data.get('items', [])
    if not items:
        return JsonResponse({'error': 'لا توجد بنود في الفاتورة'}, status=400)

    client_id = data.get('client_id')
    client = Client.objects.filter(pk=client_id, center=center).first() if client_id else None

    payment_method = data.get('payment_method', 'cash')
    discount_amount = Decimal(str(data.get('discount', 0) or 0))
    notes = data.get('notes', '')

    from apps.core.models import Settings
    settings_obj, _ = Settings.objects.get_or_create(center=center)
    number = settings_obj.next_invoice_number()

    inv = Invoice.objects.create(
        center=center,
        number=number,
        client=client,
        payment_method=payment_method,
        discount_amount=discount_amount,
        notes=notes,
        status='draft',
    )

    for item in items:
        svc = Service.objects.filter(pk=item.get('service_id'), center=center).first() if item.get('service_id') else None
        prd = Product.objects.filter(pk=item.get('product_id'), center=center).first() if item.get('product_id') else None
        qty = Decimal(str(item.get('qty', 1)))

        InvoiceLine.objects.create(
            invoice=inv,
            description=item.get('name', '—'),
            service=svc,
            product=prd,
            quantity=qty,
            unit_price=Decimal(str(item.get('price', 0))),
            discount_percent=Decimal('0'),
        )

        if prd:
            StockMovement.objects.create(
                center=center,
                product=prd,
                change=-qty,
                type='sale',
                reference=f'invoice_{inv.pk}',
                notes=f'POS {number}',
            )

    inv.recalculate()

    if payment_method != 'later':
        inv.mark_paid(amount=inv.total, method=payment_method)
        _create_invoice_treasury_movement(inv)

    return JsonResponse({
        'ok': True,
        'invoice_pk': inv.pk,
        'invoice_number': inv.number,
        'print_url': f'/billing/{inv.pk}/print/',
    })
