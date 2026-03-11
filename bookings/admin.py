from django.contrib import admin
from .models import Booking, BookingItem


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    fields = ['service_item', 'quantity', 'price']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'service', 'car_model', 'wheel_diameter', 'status', 'scheduled_at', 'created_at']
    list_filter = ['status', 'created_at', 'scheduled_at', 'wheel_diameter']
    search_fields = ['user__email', 'service__title', 'car_model']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BookingItemInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'service', 'status', 'scheduled_at')
        }),
        ('Информация об автомобиле', {
            'fields': ('car_model', 'wheel_diameter')
        }),
        ('Системные поля', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ['booking', 'service_item', 'quantity', 'price']
    search_fields = ['booking__id', 'service_item__name']
    readonly_fields = ['booking', 'service_item']
