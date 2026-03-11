#!/usr/bin/env python
"""
Отладка проблемы с бронированиями
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization, City
from services.models import Service
from bookings.models import Booking
from django.utils import timezone
from datetime import timedelta

def debug_bookings():
    print("=== Отладка бронирований ===")
    
    # Проверяем пользователей
    print("\n=== Пользователи ===")
    users = User.objects.all()
    for user in users:
        print(f"- {user.email}: role={user.role}")
    
    # Проверяем организации
    print("\n=== Организации ===")
    orgs = Organization.objects.all()
    for org in orgs:
        print(f"- {org.name}: owner={org.owner.email} (role={org.owner.role})")
    
    # Проверяем услуги
    print("\n=== Услуги ===")
    services = Service.objects.all()
    for service in services:
        print(f"- {service.title}: org={service.organization.name}, owner={service.organization.owner.email}")
    
    # Проверяем бронирования
    print("\n=== Бронирования ===")
    bookings = Booking.objects.all()
    for booking in bookings:
        print(f"- Booking #{booking.id}: user={booking.user.email}, service={booking.service.title}, org_owner={booking.service.organization.owner.email}")
    
    print(f"\nВсего бронирований: {bookings.count()}")
    
    # Создадим тестовое бронирование если его нет
    if bookings.count() == 0:
        print("\n=== Создаем тестовое бронирование ===")
        
        # Найдем пользователя-клиента
        client = User.objects.filter(role='CLIENT').first()
        if not client:
            client = User.objects.create(
                email='client@test.com',
                role='CLIENT',
                name='Test Client'
            )
            print(f"Создан клиент: {client.email}")
        
        # Найдем услугу
        service = Service.objects.first()
        if service:
            booking = Booking.objects.create(
                user=client,
                service=service,
                status='NEW',
                scheduled_at=timezone.now() + timedelta(days=1)
            )
            print(f"Создано бронирование: {booking}")
        else:
            print("Нет услуг для создания бронирования")
    
    # Проверим логику фильтрации для разных ролей
    print("\n=== Тестирование логики фильтрации ===")
    
    for user in User.objects.all():
        print(f"\nДля пользователя {user.email} (role={user.role}):")
        
        if user.role == 'ADMIN':
            queryset = Booking.objects.all()
        elif user.role == 'ORGANIZATION':
            queryset = Booking.objects.filter(service__organization__owner=user)
        else:
            queryset = Booking.objects.filter(user=user)
        
        print(f"  Видит бронирований: {queryset.count()}")
        for booking in queryset:
            print(f"    - Booking #{booking.id}: {booking.service.title}")

if __name__ == '__main__':
    debug_bookings()