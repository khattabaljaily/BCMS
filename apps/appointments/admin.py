from django.contrib import admin
from .models import Appointment, AppointmentService

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client_display', 'date', 'start_time', 'specialist', 'status', 'total_price']
    list_filter = ['center', 'status', 'date']
    search_fields = ['client__name', 'walk_in_name']
