from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'center', 'gender', 'points', 'created_at']
    list_filter = ['center', 'gender']
    search_fields = ['name', 'phone']
