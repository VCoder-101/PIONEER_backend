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
        """
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