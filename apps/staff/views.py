from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Specialist
from apps.services.models import Service


@login_required
def specialist_list(request):
    center = request.center
    specialists = Specialist.objects.filter(center=center).prefetch_related('services').order_by('order', 'name')
    services = Service.objects.filter(center=center, is_active=True).select_related('category').order_by('name')
    return render(request, 'staff/list.html', {
        'specialists': specialists,
        'services': services,
    })


@login_required
def specialist_save(request, pk=None):
    center = request.center
    instance = get_object_or_404(Specialist, pk=pk, center=center) if pk else None
    services = Service.objects.filter(center=center, is_active=True).select_related('category')

    if request.method == 'POST':
        data = request.POST
        if instance is None:
            instance = Specialist(center=center)
        instance.name      = data.get('name', '').strip()
        instance.phone     = data.get('phone', '').strip()
        instance.specialty = data.get('specialty', '').strip()
        instance.bio       = data.get('bio', '').strip()
        if 'color' in data:
            instance.color = data.get('color', '#6366f1')
        elif instance.pk is None:
            instance.color = '#6366f1'
        instance.work_start = data.get('work_start') or None
        instance.work_end   = data.get('work_end') or None
        instance.is_active  = 'is_active' in data
        instance.order      = int(data.get('order') or 0)
        if 'photo' in request.FILES:
            instance.photo = request.FILES['photo']
        instance.save()
        service_ids = data.getlist('services')
        instance.services.set(service_ids)
        if pk:
            messages.success(request, 'تم تحديث عضو الفريق بنجاح.')
        else:
            messages.success(request, 'تم إضافة عضو فريق جديد بنجاح.')
        return redirect('staff:list')

    return render(request, 'staff/form.html', {
        'instance': instance,
        'services': services,
        'selected_ids': list(instance.services.values_list('id', flat=True)) if instance else [],
    })


@login_required
def specialist_delete(request, pk):
    obj = get_object_or_404(Specialist, pk=pk, center=request.center)
    if request.method == 'POST':
        obj.is_active = False
        obj.save(update_fields=['is_active'])
        messages.success(request, 'تم حذف عضو الفريق بنجاح.')
    return redirect('staff:list')
