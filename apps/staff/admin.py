from django.contrib import admin
from .models import Specialist

@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ['name', 'center', 'specialty', 'is_active']
    list_filter = ['center', 'is_active']
