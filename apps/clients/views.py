from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from .models import Client
from django.template.loader import render_to_string


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
def client_list(request):
    center = request.center
    q = request.GET.get('q', '')
    clients = Client.objects.filter(center=center).annotate(
        claims_amount=Sum('invoices__total', filter=Q(invoices__status__in=['draft', 'partial']))
    )
    if q:
        clients = clients.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, 'clients/list.html', {'clients': clients, 'q': q})


@login_required
def client_detail(request, pk):
    from apps.finance.models import ClientPayment
    client       = get_object_or_404(Client, pk=pk, center=request.center)
    appointments = client.appointments.select_related('specialist').prefetch_related('appointment_services__service').order_by('-date', '-start_time')[:20]
    invoices     = client.invoices.order_by('-created_at')[:15]
    payments     = ClientPayment.objects.filter(client=client, center=request.center).select_related('invoice').order_by('-date')[:15]
    return render(request, 'clients/detail.html', {
        'client':       client,
        'appointments': appointments,
        'invoices':     invoices,
        'payments':     payments,
    })


@login_required
def client_save(request):
    center = request.center
    if request.method == 'GET':
        pk = request.GET.get('pk')
        obj = get_object_or_404(Client, pk=pk, center=center) if pk else None
        return render(request, 'clients/form.html', {'instance': obj})

    pk = request.POST.get('pk')
    obj = get_object_or_404(Client, pk=pk, center=center) if pk else Client(center=center)
    obj.name      = request.POST.get('name', '').strip()
    obj.phone     = request.POST.get('phone', '').strip()
    obj.email     = request.POST.get('email', '').strip()
    obj.birthdate = request.POST.get('birthdate') or None
    obj.notes     = request.POST.get('notes', '').strip()
    obj.referral  = request.POST.get('referral', '')

    ajax = _is_ajax(request)
    if Client.objects.filter(center=center, phone=obj.phone).exclude(pk=obj.pk if obj.pk else None).exists():
        err = 'رقم الهاتف موجود بالفعل لعميل آخر.'
        if ajax:
            return JsonResponse({'success': False, 'error': err})
        messages.error(request, err)
        return redirect('clients:list')

    obj.save()
    if ajax:
        try:
            row_html = render_to_string('clients/_row.html', {'cl': obj}, request=request)
            card_html = render_to_string('clients/_card.html', {'cl': obj}, request=request)
        except Exception:
            row_html = ''
            card_html = ''
        return JsonResponse({
            'success': True,
            'message': 'تم حفظ بيانات العميل بنجاح.',
            'row_id': 'row-%s' % obj.pk,
            'row_html': row_html,
            'card_html': card_html,
        })
    messages.success(request, 'تم الحفظ.')
    return redirect('clients:list')


@login_required
def client_delete(request, pk):
    obj = get_object_or_404(Client, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف العميل بنجاح.'})
        messages.success(request, 'تم الحذف.')
        return redirect('clients:list')
    return redirect('clients:detail', pk=pk)
