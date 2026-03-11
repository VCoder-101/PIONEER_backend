from rest_framework import serializers
from .models import Service, ServiceItem


class ServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceItem
        fields = ['id', 'service', 'name', 'description', 'price', 'is_required', 'is_active', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    items = ServiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'organization', 'organization_name', 'title', 'description', 'price', 'duration', 'status', 'is_active', 'items', 'created_at']
        read_only_fields = ['id', 'created_at']
