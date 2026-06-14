from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Treasury, TreasuryMovement, Expense, ClientPayment
from apps.billing.models import Invoice
from apps.clients.models import Client
from django.urls import reverse
from django.db.utils import OperationalError
from decimal import Decimal
from django.http import JsonResponse, HttpResponseForbidden


# ── helpers ──────────────────────────────────────────────────────────────────

def _expense_ref(pk):
    return f'expense_{pk}'

def _payment_ref(pk):
    return f'payment_{pk}'

def _create_expense_movement(expense):
    """Record a cash expense as a treasury outflow. No-op if not cash or no treasury."""
    if expense.method != 'cash' or not expense.treasury:
        return
    TreasuryMovement.objects.create(
        treasury=expense.treasury,
        type='out',
        amount=expense.amount,
        reference=_expense_ref(expense.pk),
        notes=expense.category,
    )

def _delete_expense_movement(expense):
    """Remove the treasury movement recorded for this expense (if any)."""
    for tm in TreasuryMovement.objects.filter(
        treasury__center=expense.center,
        reference=_expense_ref(expense.pk),
    ):
        tm.delete()

def _create_payment_movement(payment):
    """Record a cash client payment as a treasury inflow."""
    if payment.method != 'cash':
        return
    treasury = Treasury.objects.filter(center=payment.center).first()
    if not treasury:
        return
    TreasuryMovement.objects.create(
        treasury=treasury,
        type='in',
        amount=payment.amount,
        reference=_payment_ref(payment.pk),
        notes=f'دفعة فاتورة {payment.invoice.number if payment.invoice else payment.pk}',
    )

def _delete_payment_movement(payment):
    """Remove the treasury movement recorded for this payment."""
    for tm in TreasuryMovement.objects.filter(
        treasury__center=payment.center,
        reference=_payment_ref(payment.pk),
    ):
        tm.delete()

def _reverse_payment_movement(payment):
    """Create a reversal treasury movement for a cancelled payment (audit trail)."""
    for tm in TreasuryMovement.objects.filter(
        treasury__center=payment.center,
        reference=_payment_ref(payment.pk),
    ):
        opposite = 'out' if tm.type == 'in' else 'in'
        TreasuryMovement.objects.create(
            treasury=tm.treasury,
            type=opposite,
            amount=tm.amount,
            reference=f'rev_{tm.reference}',
            notes=f'إلغاء دفعة {payment.pk}',
        )

def _reverse_expense_movement(expense):
    """Create a reversal treasury movement for a deleted expense (audit trail)."""
    for tm in TreasuryMovement.objects.filter(
        treasury__center=expense.center,
        reference=_expense_ref(expense.pk),
    ):
        opposite = 'out' if tm.type == 'in' else 'in'
        TreasuryMovement.objects.create(
            treasury=tm.treasury,
            type=opposite,
            amount=tm.amount,
            reference=f'rev_{tm.reference}',
            notes=f'حذف مصروف: {expense.category}',
        )


# ── treasury ──────────────────────────────────────────────────────────────────

@login_required
def treasury_list(request):
    try:
        center = request.center
        treasuries = Treasury.objects.filter(center=center)
        return render(request, 'finance/treasury_list.html', {'treasuries': treasuries})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def treasury_detail(request, pk):
    try:
        from django.db.models import Sum
        treasury  = get_object_or_404(Treasury, pk=pk, center=request.center)
        raw_movements = list(treasury.movements.order_by('created_at'))

        total_in  = sum(m.amount for m in raw_movements if m.type in ('in', 'initial'))
        total_out = sum(m.amount for m in raw_movements if m.type == 'out')

        running = Decimal('0')
        movements = []
        for m in raw_movements:
            if m.type in ('in', 'initial'):
                running += m.amount
            else:
                running -= m.amount
            movements.append({'obj': m, 'balance': running})
        movements.reverse()

        return render(request, 'finance/treasury_detail.html', {
            'treasury':  treasury,
            'movements': movements,
            'total_in':  total_in,
            'total_out': total_out,
        })
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def treasury_initial_balance(request, pk):
    try:
        treasury = get_object_or_404(Treasury, pk=pk, center=request.center)
        if request.method == 'POST':
            amount = Decimal(request.POST.get('initial_balance') or '0')
            notes  = request.POST.get('notes', '')
            treasury.set_initial_balance(amount, notes)
            return redirect(reverse('finance:treasury_detail', args=[treasury.pk]))
        return render(request, 'finance/treasury_initial_balance.html', {'treasury': treasury})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


# ── expenses ──────────────────────────────────────────────────────────────────

@login_required
def expense_list(request):
    try:
        center   = request.center
        expenses = Expense.objects.filter(center=center)
        return render(request, 'finance/expense_list.html', {'expenses': expenses})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def expense_create(request):
    try:
        center = request.center
        if request.method == 'POST':
            cat      = request.POST.get('category')
            amt      = Decimal(request.POST.get('amount') or '0')
            method   = request.POST.get('method', 'cash')
            tid      = request.POST.get('treasury') or None
            treasury = Treasury.objects.filter(pk=tid, center=center).first() if tid else None
            notes    = request.POST.get('notes', '')
            if not treasury:
                err = 'يجب اختيار الخزينة'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                treasuries = Treasury.objects.filter(center=center)
                categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
                return render(request, 'finance/expense_form.html', {'treasuries': treasuries, 'categories': categories})
            if method == 'cash' and treasury.balance < amt:
                err = f'رصيد الخزينة غير كافٍ — المتاح: {treasury.balance}'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                treasuries = Treasury.objects.filter(center=center)
                categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
                return render(request, 'finance/expense_form.html', {'treasuries': treasuries, 'categories': categories})
            exp = Expense.objects.create(
                center=center, category=cat, amount=amt,
                method=method, treasury=treasury, notes=notes,
            )
            _create_expense_movement(exp)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'تم حفظ المصروف بنجاح.'})
            return redirect('finance:expenses')

        treasuries = Treasury.objects.filter(center=center)
        categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
        is_modal   = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
        template   = 'finance/partials/expense_form_partial.html' if is_modal else 'finance/expense_form.html'
        return render(request, template, {'treasuries': treasuries, 'categories': categories})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def expense_edit(request, pk):
    try:
        center = request.center
        exp    = get_object_or_404(Expense, pk=pk, center=center)
        if request.method == 'POST':
            new_amt  = Decimal(request.POST.get('amount') or '0')
            method   = request.POST.get('method', 'cash')
            tid      = request.POST.get('treasury') or None
            treasury = Treasury.objects.filter(pk=tid, center=center).first() if tid else None

            if not treasury:
                err = 'يجب اختيار الخزينة'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': err}, status=400)
                messages.error(request, err)
                treasuries = Treasury.objects.filter(center=center)
                categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
                return render(request, 'finance/expense_form.html', {'expense': exp, 'treasuries': treasuries, 'categories': categories})

            # Remove old movement first so the balance reflects the refund
            _delete_expense_movement(exp)

            if method == 'cash':
                treasury.refresh_from_db()
                if treasury.balance < new_amt:
                    # Restore the old movement since we're aborting
                    _create_expense_movement(exp)
                    err = f'رصيد الخزينة غير كافٍ — المتاح: {treasury.balance}'
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': err}, status=400)
                    messages.error(request, err)
                    treasuries = Treasury.objects.filter(center=center)
                    categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
                    return render(request, 'finance/expense_form.html', {'expense': exp, 'treasuries': treasuries, 'categories': categories})

            exp.category = request.POST.get('category')
            exp.amount   = new_amt
            exp.method   = method
            exp.treasury = treasury
            exp.notes    = request.POST.get('notes', '')
            exp.save()

            # create updated movement
            _create_expense_movement(exp)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'تم تحديث المصروف بنجاح.'})
            return redirect('finance:expenses')

        treasuries = Treasury.objects.filter(center=center)
        categories = Expense.objects.filter(center=center).values_list('category', flat=True).distinct().order_by('category')
        is_modal   = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
        template   = 'finance/partials/expense_form_partial.html' if is_modal else 'finance/expense_form.html'
        return render(request, template, {'expense': exp, 'treasuries': treasuries, 'categories': categories})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def expense_delete(request, pk):
    try:
        if request.method != 'POST':
            return HttpResponseForbidden()
        center = request.center
        exp    = get_object_or_404(Expense, pk=pk, center=center)
        _reverse_expense_movement(exp)
        exp.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'تم حذف المصروف بنجاح.'})
        return redirect('finance:expenses')
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


# ── client payments ────────────────────────────────────────────────────────────

@login_required
def client_payments_list(request):
    try:
        center   = request.center
        payments = ClientPayment.objects.filter(center=center, status='confirmed').select_related('invoice', 'client')
        return render(request, 'finance/client_payments.html', {'payments': payments})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def client_payment_create(request):
    try:
        center = request.center
        if request.method == 'POST':
            inv_id  = request.POST.get('invoice')
            amt     = Decimal(request.POST.get('amount') or '0')
            method  = request.POST.get('method', '')
            invoice = Invoice.objects.filter(pk=inv_id, center=center).first()
            client  = invoice.client if invoice and invoice.client else None
            payment = ClientPayment.objects.create(
                center=center, invoice=invoice, client=client,
                amount=amt, method=method,
            )
            if invoice:
                invoice.paid_amount += amt
                invoice.status = 'paid' if invoice.paid_amount >= invoice.total else 'partial'
                invoice.save(update_fields=['paid_amount', 'status'])
            _create_payment_movement(payment)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'تم تسجيل الدفعة بنجاح.'})
            return redirect('finance:client_payments')

        invoices = Invoice.objects.filter(center=center).exclude(status='paid')
        is_modal = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
        template = 'finance/partials/client_payment_form_partial.html' if is_modal else 'finance/client_payment_form.html'
        return render(request, template, {'invoices': invoices})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def client_payment_edit(request, pk):
    try:
        center = request.center
        pay    = get_object_or_404(ClientPayment, pk=pk, center=center)
        if request.method == 'POST':
            old_invoice = pay.invoice
            old_amount  = pay.amount

            # remove old treasury movement
            _delete_payment_movement(pay)

            inv_id  = request.POST.get('invoice')
            amt     = Decimal(request.POST.get('amount') or '0')
            method  = request.POST.get('method', '')
            invoice = Invoice.objects.filter(pk=inv_id, center=center).first()
            pay.invoice = invoice
            pay.client  = invoice.client if invoice and invoice.client else None
            pay.amount  = amt
            pay.method  = method
            pay.save()

            # adjust old invoice paid_amount
            if old_invoice and old_invoice != invoice:
                old_invoice.paid_amount = max(old_invoice.paid_amount - old_amount, Decimal('0'))
                old_invoice.status = (
                    'paid'    if old_invoice.paid_amount >= old_invoice.total else
                    'partial' if old_invoice.paid_amount > 0 else 'draft'
                )
                old_invoice.save(update_fields=['paid_amount', 'status'])
                if invoice:
                    invoice.paid_amount += amt
                    invoice.status = 'paid' if invoice.paid_amount >= invoice.total else 'partial'
                    invoice.save(update_fields=['paid_amount', 'status'])
            elif invoice:
                diff = amt - old_amount
                if diff != 0:
                    invoice.paid_amount = max(invoice.paid_amount + diff, Decimal('0'))
                    invoice.status = (
                        'paid'    if invoice.paid_amount >= invoice.total else
                        'partial' if invoice.paid_amount > 0 else 'draft'
                    )
                    invoice.save(update_fields=['paid_amount', 'status'])

            # create updated treasury movement
            _create_payment_movement(pay)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'تم تحديث الدفعة بنجاح.'})
            return redirect('finance:client_payments')

        invoices = Invoice.objects.filter(center=center).exclude(status='paid') | Invoice.objects.filter(pk=pay.invoice_id)
        is_modal = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
        template = 'finance/partials/client_payment_form_partial.html' if is_modal else 'finance/client_payment_form.html'
        return render(request, template, {'payment': pay, 'invoices': invoices})
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def client_payment_delete(request, pk):
    try:
        if request.method != 'POST':
            return HttpResponseForbidden()
        center = request.center
        pay    = get_object_or_404(ClientPayment, pk=pk, center=center)
        _reverse_payment_movement(pay)
        pay.cancel()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'تم إلغاء الدفعة بنجاح.'})
        return redirect('finance:client_payments')
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})


@login_required
def client_statement(request):
    try:
        from datetime import datetime, time as dt_time
        center  = request.center
        clients = Client.objects.filter(center=center).order_by('name')
        client  = None
        entries = []
        total_invoiced = Decimal('0')
        total_paid     = Decimal('0')
        cid = request.GET.get('client')
        if cid:
            client   = get_object_or_404(Client, pk=cid, center=center)
            invoices = Invoice.objects.filter(center=center, client=client).order_by('date', 'created_at')
            payments = ClientPayment.objects.filter(center=center, client=client).order_by('date', 'created_at')

            raw = []
            for inv in invoices:
                dt = getattr(inv, 'created_at', None) or datetime.combine(inv.date, dt_time.min)
                raw.append({'type': 'invoice', 'datetime': dt, 'obj': inv})
            for p in payments:
                dt = getattr(p, 'created_at', None) or datetime.combine(p.date, dt_time.min)
                if p.status == 'confirmed':
                    raw.append({'type': 'payment', 'datetime': dt, 'obj': p})
                else:
                    # Show original payment AND a reversal entry for cancelled payments
                    raw.append({'type': 'payment',   'datetime': dt, 'obj': p, 'cancelled': True})
                    raw.append({'type': 'reversal',  'datetime': dt, 'obj': p, 'cancelled': False})
            raw.sort(key=lambda x: x['datetime'])

            running = Decimal('0')
            for e in raw:
                e.setdefault('cancelled', False)
                if e['type'] == 'invoice':
                    amt = e['obj'].total
                    running += amt
                    total_invoiced += amt
                    e['debit']  = amt
                    e['credit'] = None
                elif e['type'] == 'payment':
                    amt = e['obj'].amount
                    running -= amt
                    if not e['cancelled']:
                        total_paid += amt
                    e['debit']  = None
                    e['credit'] = amt
                else:  # reversal
                    amt = e['obj'].amount
                    running += amt
                    e['debit']  = amt
                    e['credit'] = None
                e['balance'] = running
            entries = raw

        return render(request, 'finance/client_statement.html', {
            'clients':        clients,
            'client':         client,
            'entries':        entries,
            'total_invoiced': total_invoiced,
            'total_paid':     total_paid,
            'balance':        total_invoiced - total_paid,
        })
    except OperationalError as exc:
        return render(request, 'finance/error.html', {'error': str(exc)})
