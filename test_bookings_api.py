#!/usr/bin/env python
"""
Тест API бронирований
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from django.db import models

def test_bookings_api():
    print("=== Тест API бронирований ===")
    
    # Найдем владельца организации
    org_owner = User.objects.filter(organizations__isnull=False).first()
    
    if org_owner:
        print(f"Тестируем для владельца организации: {org_owner.email}")
        
        # Симулируем логику из BookingViewSet.get_queryset()
        user = org_owner
        if user.role == 'ADMIN':
            queryset = Booking.objects.all()
        else:
            user_organizations = user.organizations.all()
            if user_organizations.exists():
                queryset = Booking.objects.filter(
                    models.Q(service__organization__owner=user) | 
                    models.Q(user=user)
                ).distinct()
            else:
                queryset = Booking.objects.filter(user=user)
        
        print(f"Queryset содержит: {queryset.count()} бронирований")
        
        # Сериализуем результат
        serializer = BookingSerializer(queryset, many=True)
        
        print("\n=== API Response ===")
        import json
        api_response = {
            "count": queryset.count(),
            "next": None,
            "previous": None,
            "results": serializer.data
        }
        print(json.dumps(api_response, indent=2, ensure_ascii=False, default=str))
    
    # Тест для обычного клиента
    client = User.objects.filter(role='CLIENT', organizations__isnull=True).first()
    if client:
        print(f"\n=== Тест для клиента: {client.email} ===")
        
        user = client
        if user.role == 'ADMIN':
            queryset = Booking.objects.all()
        else:
            user_organizations = user.organizations.all()
            if user_organizations.exists():
                queryset = Booking.objects.filter(
                    models.Q(service__organization__owner=user) | 
                    models.Q(user=user)
                ).distinct()
            else:
                queryset = Booking.objects.filter(user=user)
        
        print(f"Клиент видит: {queryset.count()} бронирований")
        for booking in queryset:
            print(f"  - Booking #{booking.id}: {booking.service.title}")

if __name__ == '__main__':
    test_bookings_api()