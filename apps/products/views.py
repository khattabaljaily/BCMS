import json as _json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, ProductCategory, StockMovement, PurchaseInvoice, PurchaseInvoiceLine
from django.template.loader import render_to_string


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
def product_list(request):
    center = request.center
    q = request.GET.get('q', '')
    cat_id = request.GET.get('cat', '')
    products = Product.objects.filter(center=center, is_active=True).select_related('category')
    categories = ProductCategory.objects.filter(center=center, is_active=True)
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    if cat_id:
        products = products.filter(category_id=cat_id)
    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'selected_cat': cat_id,
    })


@login_required
def product_save(request, pk=None):
    center = request.center
    instance = get_object_or_404(Product, pk=pk, center=center) if pk else None
    categories = ProductCategory.objects.filter(center=center, is_active=True)

    if request.method == 'POST':
        data = request.POST
        if instance is None:
            instance = Product(center=center)
        instance.name          = data.get('name', '').strip()
        instance.description   = data.get('description', '').strip()
        instance.sku           = data.get('sku', '').strip()
        instance.category_id   = data.get('category') or None
        instance.price         = data.get('price') or 0
        instance.cost          = data.get('cost') or 0
        instance.stock         = data.get('stock') or 0
        instance.min_stock     = data.get('min_stock') or 5
        instance.is_active     = 'is_active' in data
        instance.show_in_store = 'show_in_store' in data
        if 'image' in request.FILES:
            instance.image = request.FILES['image']
        instance.save()
        if _is_ajax(request):
            try:
                row_html = render_to_string('products/_row.html', {'p': instance}, request=request)
                card_html = render_to_string('products/_card.html', {'p': instance}, request=request)
            except Exception:
                row_html = ''
                card_html = ''
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ المنتج بنجاح.',
                'row_id': 'row-%s' % instance.pk,
                'row_html': row_html,
                'card_html': card_html,
            })
        return redirect('products:list')

    return render(request, 'products/form.html', {
        'instance': instance,
        'categories': categories,
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, center=request.center)
    if request.method == 'POST':
        product.is_active = False
        product.save(update_fields=['is_active'])
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف المنتج بنجاح.', 'row_id': 'row-%s' % product.pk})
    return redirect('products:list')


@login_required
def category_list(request):
    center = request.center
    categories = ProductCategory.objects.filter(center=center).order_by('order')
    return render(request, 'products/categories.html', {'categories': categories})


@login_required
def category_save(request):
    center = request.center
    pk = request.POST.get('pk')
    obj = get_object_or_404(ProductCategory, pk=pk, center=center) if pk else ProductCategory(center=center)
    obj.name = request.POST.get('name', '').strip()
    obj.order = int(request.POST.get('order', 0))
    obj.is_active = 'is_active' in request.POST
    obj.save()
    if _is_ajax(request):
        return JsonResponse({'success': True, 'message': 'تم حفظ التصنيف بنجاح.'})
    messages.success(request, 'تم الحفظ.')
    return redirect('products:categories')


@login_required
def category_delete(request, pk):
    obj = get_object_or_404(ProductCategory, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف التصنيف بنجاح.'})
        messages.success(request, 'تم الحذف.')
    return redirect('products:categories')


@login_required
def stock_list(request):
    center = request.center
    movements = StockMovement.objects.filter(product__center=center).select_related('product')[:200]
    return render(request, 'products/stock_list.html', {'movements': movements})


@login_required
def stock_summary(request):
    center = request.center
    # list products with current stock quantities
    products = Product.objects.filter(center=center).order_by('name')
    return render(request, 'products/stock_summary.html', {'products': products})


# ── helpers ──────────────────────────────────────────────────────────────────

def _purchase_ref(pk):
    return f'purchase_{pk}'

def _next_purchase_number(center):
    from django.utils import timezone
    year  = timezone.localdate().year
    count = PurchaseInvoice.objects.filter(center=center).count() + 1
    return f'PUR-{year}-{count:04d}'

def _products_json(products):
    return _json.dumps([{
        'id': p.pk, 'name': p.name,
        'cost': float(p.cost), 'stock': float(p.stock),
        'sku': p.sku or '',
    } for p in products])

def _apply_purchase_effects(invoice):
    """Create StockMovements and treasury movement for a purchase invoice."""
    from apps.finance.models import Treasury, TreasuryMovement
    center = invoice.center
    ref    = _purchase_ref(invoice.pk)
    for line in invoice.lines.select_related('product'):
        StockMovement.objects.create(
            center=center, product=line.product,
            change=line.quantity, type='purchase',
            reference=ref,
            notes=invoice.supplier or '',
        )
        line.product.cost = line.unit_cost
        line.product.save(update_fields=['cost'])
    if invoice.payment_method == 'cash':
        treasury = Treasury.objects.filter(center=center).first()
        if treasury:
            TreasuryMovement.objects.create(
                treasury=treasury, type='out',
                amount=invoice.total,
                reference=ref,
                notes=f'مشتريات {invoice.number}',
            )

def _purchase_pay_ref(pk):
    return f'purchase_pay_{pk}'

def _reverse_purchase_effects(invoice):
    """Remove StockMovements and all treasury movements for a purchase invoice."""
    from apps.finance.models import TreasuryMovement
    ref = _purchase_ref(invoice.pk)
    for mv in StockMovement.objects.filter(product__center=invoice.center, reference=ref):
        mv.delete()
    # Cash purchase: treasury out-movement created at purchase time
    for tm in TreasuryMovement.objects.filter(treasury__center=invoice.center, reference=ref):
        tm.delete()
    # Credit purchase: treasury out-movement created when payment was recorded
    for tm in TreasuryMovement.objects.filter(treasury__center=invoice.center, reference=_purchase_pay_ref(invoice.pk)):
        tm.delete()


# ── purchase views ────────────────────────────────────────────────────────────

@login_required
def purchase_list(request):
    center    = request.center
    purchases = PurchaseInvoice.objects.filter(center=center).prefetch_related('lines__product')
    return render(request, 'products/purchase_list.html', {'purchases': purchases})


@login_required
def purchase_create(request):
    center   = request.center
    all_products = Product.objects.filter(center=center, is_active=True).select_related('category').order_by('name')

    if request.method == 'POST':
        product_ids = request.POST.getlist('product_id[]')
        quantities  = request.POST.getlist('quantity[]')
        unit_costs  = request.POST.getlist('cost[]')

        lines_data = []
        for i, pid in enumerate(product_ids):
            if not pid:
                continue
            try:
                qty  = Decimal(quantities[i]  if i < len(quantities)  else '0')
                cost = Decimal(unit_costs[i]  if i < len(unit_costs)  else '0')
            except Exception:
                continue
            if qty <= 0:
                continue
            product = Product.objects.filter(pk=pid, center=center).first()
            if product:
                lines_data.append((product, qty, cost))

        if not lines_data:
            messages.error(request, 'أضف بنداً واحداً على الأقل.')
            return render(request, 'products/purchase_form.html', {
                'all_products': all_products,
                'products_json': _products_json(all_products),
            })

        inv = PurchaseInvoice.objects.create(
            center=center,
            number=_next_purchase_number(center),
            supplier=request.POST.get('supplier', '').strip(),
            payment_method=request.POST.get('payment_method', 'cash'),
            notes=request.POST.get('notes', '').strip(),
        )
        for product, qty, cost in lines_data:
            PurchaseInvoiceLine.objects.create(
                invoice=inv, product=product,
                quantity=qty, unit_cost=cost,
            )
        inv.recalculate()
        _apply_purchase_effects(inv)
        messages.success(request, f'تم إنشاء فاتورة المشتريات {inv.number}.')
        return redirect('products:purchase_detail', pk=inv.pk)

    return render(request, 'products/purchase_form.html', {
        'all_products': all_products,
        'products_json': _products_json(all_products),
    })


@login_required
def purchase_detail(request, pk):
    inv = get_object_or_404(PurchaseInvoice, pk=pk, center=request.center)
    from apps.finance.models import Treasury
    treasuries = Treasury.objects.filter(center=request.center) if inv.payment_method == 'credit' else []
    return render(request, 'products/purchase_detail.html', {
        'inv': inv,
        'lines': inv.lines.select_related('product'),
        'treasuries': treasuries,
    })


@login_required
def purchase_pay(request, pk):
    inv = get_object_or_404(PurchaseInvoice, pk=pk, center=request.center)
    if request.method != 'POST':
        return redirect('products:purchase_detail', pk=pk)
    if inv.status == 'cancelled':
        messages.error(request, 'لا يمكن تسجيل دفع لفاتورة ملغاة.')
    elif inv.payment_method != 'credit':
        messages.error(request, 'هذه الفاتورة ليست آجلة.')
    elif inv.paid:
        messages.warning(request, 'تم تسجيل سداد هذه الفاتورة مسبقاً.')
    else:
        from apps.finance.models import Treasury, TreasuryMovement
        center = inv.center
        treasury_id = request.POST.get('treasury_id')
        treasury = Treasury.objects.filter(pk=treasury_id, center=center).first()
        if not treasury:
            treasury = Treasury.objects.filter(center=center).first()
        if treasury:
            TreasuryMovement.objects.create(
                treasury=treasury,
                type='out',
                amount=inv.total,
                reference=_purchase_pay_ref(inv.pk),
                notes=f'سداد مشتريات {inv.number}',
            )
        inv.paid = True
        inv.save(update_fields=['paid'])
        messages.success(request, f'تم تسجيل سداد الفاتورة {inv.number}.')
    return redirect('products:purchase_detail', pk=pk)


@login_required
def purchase_edit(request, pk):
    center = request.center
    inv    = get_object_or_404(PurchaseInvoice, pk=pk, center=center)
    if inv.status == 'cancelled':
        messages.error(request, 'لا يمكن تعديل فاتورة ملغاة.')
        return redirect('products:purchase_detail', pk=pk)

    all_products = Product.objects.filter(center=center, is_active=True).select_related('category').order_by('name')

    if request.method == 'POST':
        product_ids = request.POST.getlist('product_id[]')
        quantities  = request.POST.getlist('quantity[]')
        unit_costs  = request.POST.getlist('cost[]')

        lines_data = []
        for i, pid in enumerate(product_ids):
            if not pid:
                continue
            try:
                qty  = Decimal(quantities[i]  if i < len(quantities)  else '0')
                cost = Decimal(unit_costs[i]  if i < len(unit_costs)  else '0')
            except Exception:
                continue
            if qty <= 0:
                continue
            product = Product.objects.filter(pk=pid, center=center).first()
            if product:
                lines_data.append((product, qty, cost))

        if not lines_data:
            messages.error(request, 'أضف بنداً واحداً على الأقل.')
        else:
            _reverse_purchase_effects(inv)
            inv.lines.all().delete()

            inv.supplier       = request.POST.get('supplier', '').strip()
            inv.payment_method = request.POST.get('payment_method', 'cash')
            inv.notes          = request.POST.get('notes', '').strip()
            inv.save(update_fields=['supplier', 'payment_method', 'notes'])

            for product, qty, cost in lines_data:
                PurchaseInvoiceLine.objects.create(
                    invoice=inv, product=product,
                    quantity=qty, unit_cost=cost,
                )
            inv.recalculate()
            _apply_purchase_effects(inv)
            messages.success(request, 'تم تحديث الفاتورة.')
            return redirect('products:purchase_detail', pk=pk)

    existing_lines = list(inv.lines.select_related('product'))
    return render(request, 'products/purchase_form.html', {
        'inv': inv,
        'edit_mode': True,
        'existing_lines': existing_lines,
        'all_products': all_products,
        'products_json': _products_json(all_products),
    })


@login_required
def purchase_cancel(request, pk):
    inv = get_object_or_404(PurchaseInvoice, pk=pk, center=request.center)
    if request.method == 'POST':
        if inv.status == 'cancelled':
            messages.warning(request, 'الفاتورة ملغاة مسبقاً.')
        else:
            _reverse_purchase_effects(inv)
            inv.status = 'cancelled'
            inv.save(update_fields=['status'])
            messages.success(request, 'تم إلغاء الفاتورة وعكس جميع التأثيرات.')
    return redirect('products:purchase_detail', pk=pk)
