"""
Сериализаторы для управления расписанием организаций
"""
from rest_framework import serializers
from .availability_models import (
    OrganizationSchedule,
    OrganizationHoliday,
    ServiceAvailability
)


class OrganizationScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = OrganizationSchedule
        fields = [
            'id', 'organization', 'weekday', 'weekday_display',
            'is_working_day', 'open_time', 'close_time',
            'break_start', 'break_end', 'slot_duration',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Валидация времени"""
        if data.get('is_working_day'):
            open_time = data.get('open_time')
            close_time = data.get('close_time')
            
            if open_time and close_time and open_time >= close_time:
                raise serializers.ValidationError(
                    "Время закрытия должно быть позже времени открытия"
                )
            
            break_start = data.get('break_start')
            break_end = data.get('break_end')
            
            if break_start and break_end:
                if break_start >= break_end:
                    raise serializers.ValidationError(
                        "Конец перерыва должен быть позже начала"
                    )
                if break_start < open_time or break_end > close_time:
                    raise serializers.ValidationError(
                        "Перерыв должен быть в рабочее время"
                    )
            elif break_start or break_end:
                raise serializers.ValidationError(
                    "Укажите и начало, и конец перерыва"
                )
        
        return data


class OrganizationHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationHoliday
        fields = [
            'id', 'organization', 'date', 'reason',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    
    class Meta:
        model = ServiceAvailability
        fields = [
            'id', 'service', 'service_title', 'weekday', 'weekday_display',
            'available_from', 'available_to', 'max_bookings_per_slot',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        """Валидация времени доступности"""
        available_from = data.get('available_from')
        available_to = data.get('available_to')
        
        if available_from and available_to and available_from >= available_to:
            raise serializers.ValidationError(
                "Время окончания должно быть позже времени начала"
            )
        
        return data
