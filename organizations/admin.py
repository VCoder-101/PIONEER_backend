from django.contrib import admin
from .models import Organization, City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'region']
    list_filter = ['is_active', 'country']
    readonly_fields = ['created_at']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'short_name', 'organization_status', 'organization_type', 
        'owner', 'city', 'phone', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'short_name', 'owner__email', 'phone', 'org_inn', 'org_ogrn']
    list_filter = [
        'organization_status', 'organization_type', 'is_active', 
        'city', 'created_at'
    ]
    readonly_fields = ['created_at', 'organization_date_approved', 'count_services', 'summary_price']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_name', 'owner', 'description')
        }),
        ('Статус и тип', {
            'fields': ('organization_status', 'organization_date_approved', 'organization_type')
        }),
        ('Контактная информация', {
            'fields': ('city', 'address', 'phone', 'email')
        }),
        ('Государственные данные', {
            'fields': ('org_inn', 'org_ogrn', 'org_kpp')
        }),
        ('Дополнительные данные', {
            'fields': ('wheel_diameters', 'count_services', 'summary_price')
        }),
        ('Системные поля', {
            'fields': ('is_active', 'created_at')
        }),
    )
