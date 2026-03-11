#!/usr/bin/env python
"""
Тест исправленной логики бронирований
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization
from services.models import Service
from bookings.models import Booking
from django.db import models

def test_fixed_bookings():
    print("=== Тест исправленной логики бронирований ===")
    
    # Найдем владельца организации
    org_owner = User.objects.filter(organizations__isnull=False).first()
    if org_owner:
        print(f"Владелец организации: {org_owner.email}")
        
        # Новая логика для владельца организации
        user_organizations = org_owner.organizations.all()
        if user_organizations.exists():
            queryset = Booking.objects.filter(
                models.Q(service__organization__owner=org_owner) | 
                models.Q(user=org_owner)
            ).distinct()
            print(f"Владелец видит бронирований: {queryset.count()}")
            for booking in queryset:
                print(f"  - Booking #{booking.id}: {booking.service.title} (клиент: {booking.user.email})")
        
        # Создадим еще одно бронирование на услугу этого владельца
        service = Service.objects.filter(organization__owner=org_owner).first()
        if service:
            client = User.objects.filter(role='CLIENT').exclude(id=org_owner.id).first()
            if client:
                booking, created = Booking.objects.get_or_create(
                    user=client,
                    service=service,
                    defaults={
                        'status': 'NEW',
                        'scheduled_at': '2026-03-12 10:00:00'
                    }
                )
                if created:
                    print(f"Создано новое бронирование: {booking}")
                
                # Проверим снова
                queryset = Booking.objects.filter(
                    models.Q(service__organization__owner=org_owner) | 
                    models.Q(user=org_owner)
                ).distinct()
                print(f"Теперь владелец видит бронирований: {queryset.count()}")
                for booking in queryset:
                    print(f"  - Booking #{booking.id}: {booking.service.title} (клиент: {booking.user.email})")
    
    print("\n=== Проверка всех бронирований ===")
    all_bookings = Booking.objects.all()
    for booking in all_bookings:
        print(f"- Booking #{booking.id}: клиент={booking.user.email}, услуга={booking.service.title}, владелец_услуги={booking.service.organization.owner.email}")

if __name__ == '__main__':
    test_fixed_bookings()