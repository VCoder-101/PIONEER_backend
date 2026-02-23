from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSession, AuthCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone', 'role', 'is_active', 'is_staff', 'created_at', 'last_login_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('phone',)}),
        ('Информация', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Сессия', {'fields': ('current_device_id', 'current_session_id')}),
        ('Политика', {'fields': ('privacy_policy_accepted_at',)}),
        ('Даты', {'fields': ('created_at', 'last_login_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'role'),
        }),
    )
    
    readonly_fields = ['created_at', 'last_login_at', 'current_session_id']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_id', 'ip_address', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__phone', 'device_id', 'ip_address']
    readonly_fields = ['created_at']


@admin.register(AuthCode)
class AuthCodeAdmin(admin.ModelAdmin):
    list_display = ['phone', 'code', 'attempts_left', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['phone', 'code']
    readonly_fields = ['created_at']
