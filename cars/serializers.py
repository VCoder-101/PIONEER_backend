from rest_framework import serializers
from .models import Car


class CarReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения автомобиля"""
    owner_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Car
        fields = ['id', 'owner_email', 'brand', 'license_plate', 'wheel_diameter', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner_email', 'created_at', 'updated_at']


class CarWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления автомобиля"""

    class Meta:
        model = Car
        fields = ['brand', 'license_plate', 'wheel_diameter']

    def validate_license_plate(self, value):
        return value.upper().strip()

    def validate_wheel_diameter(self, value):
        if value < 10 or value > 30:
            raise serializers.ValidationError('Диаметр шины должен быть от 10 до 30 дюймов.')
        return value
