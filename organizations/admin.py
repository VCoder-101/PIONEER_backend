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
    list_display = ['name', 'owner', 'city', 'phone', 'is_active', 'created_at']
    search_fields = ['name', 'owner__email', 'phone']
    list_filter = ['is_active', 'city', 'created_at']
    readonly_fields = ['created_at']
