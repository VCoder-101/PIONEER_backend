from rest_framework import serializers
from .models import Booking, BookingItem


class BookingItemSerializer(serializers.ModelSerializer):
    service_item_name = serializers.CharField(source='service_item.name', read_only=True)

    class Meta:
        model = BookingItem
        fields = ['id', 'booking', 'service_item', 'service_item_name', 'quantity', 'price']
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    items = BookingItemSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_email', 'service', 'service_title', 'status', 'scheduled_at', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
