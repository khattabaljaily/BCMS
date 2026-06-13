from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import ServiceCategory, Service
from django.template.loader import render_to_string
from django.utils.html import escape


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
def services_home(request):
    center = request.center
    categories = ServiceCategory.objects.filter(center=center).prefetch_related('services')
    services = Service.objects.filter(center=center).select_related('category').order_by('category__order', 'order', 'name')
    return render(request, 'services/list.html', {
        'categories': categories,
        'services': services,
    })


@login_required
def category_list(request):
    center = request.center
    categories = ServiceCategory.objects.filter(center=center).order_by('order', 'name')
    return render(request, 'services/categories.html', {'categories': categories})


@login_required
def category_form(request, pk=None):
    center = request.center
    instance = get_object_or_404(ServiceCategory, pk=pk, center=center) if pk else None
    return render(request, 'services/category_form.html', {
        'instance': instance,
    })


@login_required
def category_save(request):
    center = request.center
    pk = request.POST.get('pk')
    obj = get_object_or_404(ServiceCategory, pk=pk, center=center) if pk else ServiceCategory(center=center)
    obj.name  = request.POST.get('name', '').strip()
    obj.icon  = request.POST.get('icon', obj.icon).strip()
    obj.color = request.POST.get('color', obj.color).strip()
    obj.order = int(request.POST.get('order', 0))
    obj.is_active = 'is_active' in request.POST
    obj.save()
    if _is_ajax(request):
        # return a lightweight HTML snippet to speed up AJAX responses
        try:
            name = escape(obj.name)
            desc = escape(obj.description or '')
            row_html = '<tr id="row-%s"><td><strong>%s</strong>%s</td><td>—</td><td></td><td></td><td></td><td></td><td></td></tr>' % (
                obj.pk,
                name,
                ('<br><small class="text-muted">%s</small>' % desc) if desc else ''
            )
            card_html = '<div class="cx-card" id="card-%s"><h4>%s</h4></div>' % (obj.pk, name)
        except Exception:
            row_html = ''
            card_html = ''
        return JsonResponse({'success': True, 'message': 'تم حفظ التصنيف بنجاح.', 'row_id': 'row-%s' % obj.pk, 'row_html': row_html, 'card_html': card_html})
    messages.success(request, 'تم الحفظ.')
    return redirect('services:categories')


@login_required
def category_delete(request, pk):
    obj = get_object_or_404(ServiceCategory, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف التصنيف بنجاح.', 'row_id': 'row-%s' % obj.pk})
        messages.success(request, 'تم الحذف.')
    return redirect('services:categories')


@login_required
def service_save(request):
    if request.method != 'POST':
        return redirect('services:list')
    center = request.center
    pk = request.POST.get('pk')
    obj = get_object_or_404(Service, pk=pk, center=center) if pk else Service(center=center)
    cat_id = request.POST.get('category_id') or None
    obj.category_id   = cat_id
    obj.name          = request.POST.get('name', '').strip()
    obj.description   = request.POST.get('description', '').strip()
    obj.duration      = int(request.POST.get('duration', 60))
    obj.price         = request.POST.get('price', 0)
    obj.cost          = request.POST.get('cost', 0)
    obj.show_in_store = bool(request.POST.get('show_in_store'))
    obj.is_active     = 'is_active' in request.POST
    obj.order         = int(request.POST.get('order', 0))
    obj.save()
    if _is_ajax(request):
        try:
            row_html = render_to_string('services/_row.html', {'svc': obj}, request=request)
            card_html = render_to_string('services/_card.html', {'svc': obj}, request=request)
        except Exception:
            row_html = ''
            card_html = ''
        return JsonResponse({'success': True, 'message': 'تم حفظ الخدمة بنجاح.', 'row_id': 'row-%s' % obj.pk, 'row_html': row_html, 'card_html': card_html})
    messages.success(request, 'تم الحفظ.')
    return redirect('services:list')


@login_required
def service_delete(request, pk):
    obj = get_object_or_404(Service, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.delete()
        if _is_ajax(request):
            return JsonResponse({'success': True, 'message': 'تم حذف الخدمة بنجاح.', 'row_id': 'row-%s' % obj.pk})
        messages.success(request, 'تم الحذف.')
    return redirect('services:list')
