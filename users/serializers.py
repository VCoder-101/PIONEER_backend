from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    cars = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'is_active', 'privacy_policy_accepted_at', 'created_at', 'last_login_at', 'cars']
        read_only_fields = ['id', 'created_at', 'last_login_at', 'cars']

    def get_cars(self, obj):
        from cars.models import Car
        return list(
            Car.objects.filter(user=obj).values('id', 'brand', 'license_plate', 'wheel_diameter')
        )
