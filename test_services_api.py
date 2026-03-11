#!/usr/bin/env python
"""
Тест для проверки API услуг с новым полем status
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization, City
from services.models import Service
from services.serializers import ServiceSerializer

def test_services_api():
    print("=== Тестирование API услуг ===")
    
    # Получаем существующие данные или создаем новые
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'role': 'CLIENT', 'name': 'Test User'}
    )
    print(f"Пользователь: {user.email} ({'создан' if created else 'найден'})")
    
    city, created = City.objects.get_or_create(
        name='Тестовый город',
        defaults={'region': 'Тестовый регион'}
    )
    
    org, created = Organization.objects.get_or_create(
        name='TEST ORG',
        owner=user,
        defaults={
            'short_name': 'TST',
            'organization_status': 'approved',
            'organization_type': 'wash',
            'city': city,
        }
    )
    print(f"Организация: {org.name} ({'создана' if created else 'найдена'})")
    
    # Создаем активную услугу
    active_service, created = Service.objects.get_or_create(
        title='Мойка автомобиля',
        organization=org,
        defaults={
            'description': 'Полная мойка автомобиля',
            'price': 500.00,
            'duration': 30,
            'status': 'active',
            'is_active': True
        }
    )
    print(f"Активная услуга: {active_service.title} ({'создана' if created else 'найдена'})")
    
    # Создаем скрытую услуга
    ghost_service, created = Service.objects.get_or_create(
        title='VIP мойка',
        organization=org,
        defaults={
            'description': 'Премиум мойка для VIP клиентов',
            'price': 1500.00,
            'duration': 60,
            'status': 'ghost',
            'is_active': True
        }
    )
    print(f"Скрытая услуга: {ghost_service.title} ({'создана' if created else 'найдена'})")
    
    # Тестируем сериализацию
    print("\n=== Активная услуга ===")
    active_serializer = ServiceSerializer(active_service)
    print(f"Status: {active_serializer.data['status']}")
    
    print("\n=== Скрытая услуга ===")
    ghost_serializer = ServiceSerializer(ghost_service)
    print(f"Status: {ghost_serializer.data['status']}")
    
    # Проверяем все услуги организации
    all_services = Service.objects.filter(organization=org)
    print(f"\n=== Все услуги организации ({all_services.count()}) ===")
    for service in all_services:
        print(f"- {service.title}: status={service.status}, is_active={service.is_active}")
    
    # Проверяем видимые для клиентов услуги
    client_services = Service.objects.filter(is_active=True, status='active')
    print(f"\n=== Услуги видимые клиентам ({client_services.count()}) ===")
    for service in client_services:
        print(f"- {service.title}: status={service.status}")
    
    # Тестируем полный API ответ
    print(f"\n=== Пример API ответа ===")
    import json
    serializer = ServiceSerializer(active_service)
    print(json.dumps(serializer.data, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    test_services_api()