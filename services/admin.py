from django.contrib import admin
from .models import Service, ServiceItem


class ServiceItemInline(admin.TabularInline):
    model = ServiceItem
    extra = 1
    fields = ['name', 'description', 'price', 'is_required', 'is_active', 'order']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'price', 'duration', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['title', 'organization__name']
    readonly_fields = ['created_at']
    inlines = [ServiceItemInline]


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'price', 'is_required', 'is_active', 'order']
    list_filter = ['is_required', 'is_active', 'service']
    search_fields = ['name', 'service__title']
    readonly_fields = ['created_at']
