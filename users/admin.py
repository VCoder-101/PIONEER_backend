from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'role', 'is_active', 'is_staff', 'created_at', 'last_login_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    
    # Убираем password из всех форм
    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Личная информация', {'fields': ('name',)}),
        ('Права доступа', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Сессия', {'fields': ('current_device_id', 'current_session_id')}),
        ('Политика', {'fields': ('privacy_policy_accepted_at',)}),
        ('Даты', {'fields': ('created_at', 'last_login_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'is_staff', 'is_superuser'),
        }),
    )
    
    readonly_fields = ['created_at', 'last_login_at', 'current_session_id']
    
    # Отключаем форму смены пароля
    def has_change_password_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_id', 'ip_address', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'device_id', 'ip_address']
    readonly_fields = ['created_at']
