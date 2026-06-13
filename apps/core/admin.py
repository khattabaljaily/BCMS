from django.contrib import admin
from .models import ServiceType, Center, Settings


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'order']
    list_editable = ['is_active', 'order']


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'service_type', 'plan', 'is_active', 'created_at']
    list_filter = ['plan', 'is_active', 'service_type']
    search_fields = ['name', 'slug', 'phone']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['center', 'store_enabled', 'booking_enabled', 'loyalty_enabled']
