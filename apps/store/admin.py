from django.contrib import admin
from .models import OnlineBooking, StoreOrder

@admin.register(OnlineBooking)
class OnlineBookingAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'client_phone', 'service', 'preferred_date', 'status']
    list_filter = ['center', 'status']

@admin.register(StoreOrder)
class StoreOrderAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'total', 'status', 'created_at']
    list_filter = ['center', 'status']
