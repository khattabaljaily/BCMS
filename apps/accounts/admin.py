from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'center', 'role', 'is_owner', 'is_active']
    list_filter = ['is_owner', 'is_active', 'center']
    search_fields = ['username', 'full_name', 'phone']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('بيانات شخصية', {'fields': ('full_name', 'phone', 'email', 'avatar')}),
        ('المركز والدور', {'fields': ('center', 'role', 'is_owner')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'center', 'password1', 'password2'),
        }),
    )
    ordering = ['center', 'full_name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'center', 'is_default']
    list_filter = ['center']
