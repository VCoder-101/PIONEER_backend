from django.contrib import admin
from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['brand', 'license_plate', 'wheel_diameter', 'user', 'created_at']
    list_filter = ['brand', 'wheel_diameter']
    search_fields = ['license_plate', 'brand', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
