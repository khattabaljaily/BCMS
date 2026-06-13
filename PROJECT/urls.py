from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='core')),
    path('', include('apps.accounts.urls', namespace='accounts')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('clients/', include('apps.clients.urls', namespace='clients')),
    path('staff/', include('apps.staff.urls', namespace='staff')),
    path('appointments/', include('apps.appointments.urls', namespace='appointments')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('finance/', include('apps.finance.urls', namespace='finance')),
    path('products/', include('apps.products.urls', namespace='products')),
    path('store/', include('apps.store.urls', namespace='store')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('sysadmin/', include('apps.sysadmin.urls', namespace='sysadmin')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
