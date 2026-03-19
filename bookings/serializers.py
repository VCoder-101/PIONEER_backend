from rest_framework import serializers
from .models import Booking, BookingItem


class BookingItemSerializer(serializers.ModelSerializer):
    service_item_name = serializers.CharField(source='service_item.name', read_only=True)

    class Meta:
        model = BookingItem
        fields = ['id', 'booking', 'service_item', 'service_item_name', 'quantity', 'price']
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    customerName = serializers.CharField(source='user.name', read_only=True)
    dateTime = serializers.DateTimeField(source='scheduled_at', format='%d/%m/%Y %H:%M', required=False)
    carModel = serializers.CharField(source='car_model', required=False)
    serviceMethod = serializers.CharField(source='service.title', read_only=True)
    duration = serializers.CharField(source='service.duration', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    wheelDiameter = serializers.IntegerField(source='wheel_diameter', required=False, allow_null=True)
    
    # Оригинальные поля для совместимости
    user_email = serializers.EmailField(source='user.email', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    items = BookingItemSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'customerName', 'dateTime', 'carModel', 'serviceMethod', 'duration', 'price', 'wheelDiameter',
            'user', 'user_email', 'service', 'service_title', 'status', 'scheduled_at', 'car_model', 'wheel_diameter', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Валидация данных бронирования.
        Поддерживает оба формата: camelCase и snake_case.
        Проверяет доступность времени для записи.
        """
        from datetime import datetime, timedelta
        from django.utils import timezone
        from organizations.availability_models import (
            OrganizationSchedule,
            OrganizationHoliday,
            ServiceAvailability
        )
        
        # Если используется dateTime (camelCase), копируем в scheduled_at
        if 'scheduled_at' not in data and hasattr(self, 'initial_data'):
            if 'dateTime' in self.initial_data:
                # dateTime уже обработан через source='scheduled_at'
                pass
        
        # Если используется carModel (camelCase), копируем в car_model
        if 'car_model' not in data and hasattr(self, 'initial_data'):
            if 'carModel' in self.initial_data:
                # carModel уже обработан через source='car_model'
                pass
        
        # Если используется wheelDiameter (camelCase), копируем в wheel_diameter
        if 'wheel_diameter' not in data and hasattr(self, 'initial_data'):
            if 'wheelDiameter' in self.initial_data:
                # wheelDiameter уже обработан через source='wheel_diameter'
                pass
        
        # Валидация времени записи
        scheduled_at = data.get('scheduled_at')
        service = data.get('service')
        
        if scheduled_at and service:
            # Проверяем, что время не в прошлом
            now = timezone.now()
            if scheduled_at < now:
                raise serializers.ValidationError({
                    'scheduled_at': 'Нельзя записаться на прошедшее время'
                })
            
            # Проверяем минимальное время до записи (1 час)
            min_time = now + timedelta(hours=1)
            if scheduled_at < min_time:
                raise serializers.ValidationError({
                    'scheduled_at': 'Минимальное время до записи - 1 час'
                })
            
            organization = service.organization
            weekday = scheduled_at.weekday()
            date = scheduled_at.date()
            time = scheduled_at.time()
            
            # Проверяем выходной день
            if OrganizationHoliday.objects.filter(
                organization=organization,
                date=date,
                is_active=True
            ).exists():
                raise serializers.ValidationError({
                    'scheduled_at': f'Организация не работает {date.strftime("%d.%m.%Y")}'
                })
            
            # Проверяем расписание организации
            try:
                schedule = OrganizationSchedule.objects.get(
                    organization=organization,
                    weekday=weekday,
                    is_active=True
                )
            except OrganizationSchedule.DoesNotExist:
                raise serializers.ValidationError({
                    'scheduled_at': f'Организация не работает в этот день недели'
                })
            
            if not schedule.is_working_day:
                raise serializers.ValidationError({
                    'scheduled_at': f'Организация не работает в этот день недели'
                })
            
            # Проверяем специфичное расписание услуги
            service_availability = ServiceAvailability.objects.filter(
                service=service,
                weekday=weekday,
                is_active=True
            ).first()
            
            if service_availability:
                if time < service_availability.available_from or time >= service_availability.available_to:
                    raise serializers.ValidationError({
                        'scheduled_at': f'Услуга доступна с {service_availability.available_from.strftime("%H:%M")} до {service_availability.available_to.strftime("%H:%M")}'
                    })
                max_bookings = service_availability.max_bookings_per_slot
            else:
                # Используем общее расписание организации
                if time < schedule.open_time or time >= schedule.close_time:
                    raise serializers.ValidationError({
                        'scheduled_at': f'Организация работает с {schedule.open_time.strftime("%H:%M")} до {schedule.close_time.strftime("%H:%M")}'
                    })
                
                # Проверяем перерыв
                if schedule.break_start and schedule.break_end:
                    if schedule.break_start <= time < schedule.break_end:
                        raise serializers.ValidationError({
                            'scheduled_at': f'Время попадает на перерыв ({schedule.break_start.strftime("%H:%M")} - {schedule.break_end.strftime("%H:%M")})'
                        })
                
                max_bookings = 1
            
            # Проверяем занятость слота
            existing_bookings = Booking.objects.filter(
                service=service,
                scheduled_at=scheduled_at,
                status__in=['NEW', 'CONFIRMED']
            )
            
            # Исключаем текущее бронирование при обновлении
            if self.instance:
                existing_bookings = existing_bookings.exclude(id=self.instance.id)
            
            if existing_bookings.count() >= max_bookings:
                raise serializers.ValidationError({
                    'scheduled_at': 'Это время уже занято'
                })
        
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    """Сериализатор для формата invoices (упрощенный)"""
    customerName = serializers.CharField(source='user.name', read_only=True)
    dateTime = serializers.DateTimeField(source='scheduled_at', format='%d/%m/%Y %H:%M', read_only=True)
    carModel = serializers.CharField(source='car_model', read_only=True)
    serviceMethod = serializers.CharField(source='service.title', read_only=True)
    duration = serializers.CharField(source='service.duration', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    bookingStatus = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'customerName', 'dateTime', 'carModel', 'serviceMethod', 'duration', 'price', 'status', 'bookingStatus']
    
    def get_bookingStatus(self, obj):
        """
        Определяет статус бронирования для календаря:
        - active: NEW, CONFIRMED
        - archived: CANCELLED, DONE
        """
        if obj.status in ['NEW', 'CONFIRMED']:
            return 'active'
        elif obj.status in ['CANCELLED', 'DONE']:
            return 'archived'
        return 'active'  # По умолчанию