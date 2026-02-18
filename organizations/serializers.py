from rest_framework import serializers
from .models import Organization, City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'region', 'country', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = Organization
        fields = ['id', 'name', 'owner', 'owner_email', 'city', 'city_name', 'address', 'phone', 'email', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
