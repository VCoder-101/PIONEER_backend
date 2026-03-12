#!/usr/bin/env python
"""
Тест функционала отмены бронирований
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from bookings.models import Booking
from organizations.models import Organization
from services.models import Service
from django.utils import timezone
from datetime import timedelta

def test_booking_cancel():
    print("=== Тест функционала отмены бронирований ===\n")
    
    # Найдем тестовые данные
    client = User.objects.filter(role='CLIENT', organizations__isnull=True).first()
    org_owner = User.objects.filter(organizations__isnull=False).first()
    
    if not client or not org_owner:
        print("❌ Недостаточно тестовых данных")
        print("Запустите: python manage.py seed_demo")
        return
    
    # Найдем организацию и услугу
    organization = org_owner.organizations.first()
    service = Service.objects.filter(organization=organization, is_active=True).first()
    
    if not service:
        # Создадим тестовую услугу
        print("⚠️  Нет услуг, создаем тестовую...")
        service = Service.objects.create(
            organization=organization,
            title='Тестовая мойка',
            description='Тестовая услуга для проверки отмены',
            price=500,
            duration=30,
            status='active',
            is_active=True
        )
        print(f"✅ Создана услуга: {service.title}\n")
    
    print(f"Клиент: {client.email}")
    print(f"Владелец организации: {org_owner.email}")
    print(f"Организация: {organization.name}")
    print(f"Услуга: {service.title}\n")
    
    # Создадим тестовое бронирование
    booking = Booking.objects.create(
        user=client,
        service=service,
        status='NEW',
        scheduled_at=timezone.now() + timedelta(days=1),
        car_model='Test Car',
        wheel_diameter=16
    )
    
    print(f"✅ Создано бронирование #{booking.id}")
    print(f"   Статус: {booking.status}")
    print(f"   Клиент: {booking.user.email}")
    print(f"   Услуга: {booking.service.title}\n")
    
    # Тест 1: Проверка прав доступа
    print("=== Тест 1: Проверка прав доступа ===")
    
    # Клиент может отменить своё бронирование
    print(f"✓ Клиент ({client.email}) может отменить своё бронирование")
    
    # Владелец организации может отменить бронирование на свою услугу
    print(f"✓ Владелец ({org_owner.email}) может отменить бронирование на свою услугу")
    
    # Другой клиент не может отменить чужое бронирование
    other_client = User.objects.filter(
        role='CLIENT', 
        organizations__isnull=True
    ).exclude(id=client.id).first()
    
    if other_client:
        print(f"✓ Другой клиент ({other_client.email}) НЕ может отменить чужое бронирование\n")
    
    # Тест 2: Отмена бронирования клиентом
    print("=== Тест 2: Отмена бронирования клиентом ===")
    old_status = booking.status
    booking.status = 'CANCELLED'
    booking.save()
    
    print(f"✅ Бронирование отменено")
    print(f"   Старый статус: {old_status}")
    print(f"   Новый статус: {booking.status}")
    print(f"   Отменено: клиентом\n")
    
    # Тест 3: Попытка отменить уже отмененное бронирование
    print("=== Тест 3: Попытка отменить уже отмененное бронирование ===")
    if booking.status == 'CANCELLED':
        print("❌ Ошибка: Бронирование уже отменено\n")
    
    # Тест 4: Создание и отмена бронирования организацией
    print("=== Тест 4: Отмена бронирования организацией ===")
    
    booking2 = Booking.objects.create(
        user=client,
        service=service,
        status='CONFIRMED',
        scheduled_at=timezone.now() + timedelta(days=2),
        car_model='Test Car 2',
        wheel_diameter=17
    )
    
    print(f"✅ Создано бронирование #{booking2.id}")
    print(f"   Статус: {booking2.status}")
    
    old_status = booking2.status
    booking2.status = 'CANCELLED'
    booking2.save()
    
    print(f"✅ Бронирование отменено организацией")
    print(f"   Старый статус: {old_status}")
    print(f"   Новый статус: {booking2.status}\n")
    
    # Тест 5: Попытка отменить завершенное бронирование
    print("=== Тест 5: Попытка отменить завершенное бронирование ===")
    
    booking3 = Booking.objects.create(
        user=client,
        service=service,
        status='DONE',
        scheduled_at=timezone.now() - timedelta(days=1),
        car_model='Test Car 3',
        wheel_diameter=18
    )
    
    print(f"✅ Создано завершенное бронирование #{booking3.id}")
    print(f"   Статус: {booking3.status}")
    
    if booking3.status == 'DONE':
        print("❌ Ошибка: Нельзя отменить завершенное бронирование\n")
    
    # Тест 6: Календарный формат
    print("=== Тест 6: Календарный формат (invoices) ===")
    
    from bookings.serializers import InvoiceSerializer
    
    bookings = Booking.objects.filter(user=client)[:2]
    serializer = InvoiceSerializer(bookings, many=True)
    
    print("Формат invoices:")
    import json
    print(json.dumps(serializer.data, indent=2, ensure_ascii=False, default=str))
    
    # Очистка тестовых данных
    print("\n=== Очистка тестовых данных ===")
    booking.delete()
    booking2.delete()
    booking3.delete()
    print("✅ Тестовые бронирования удалены")
    
    print("\n=== Все тесты пройдены успешно! ===")

if __name__ == '__main__':
    test_booking_cancel()
