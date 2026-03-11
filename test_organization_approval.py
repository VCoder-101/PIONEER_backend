#!/usr/bin/env python
"""
Тест системы аппрува организаций
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization, City
from organizations.serializers import OrganizationSerializer

def test_organization_approval():
    print("=== Тест системы аппрува организаций ===")
    
    # Создаем администратора
    admin, created = User.objects.get_or_create(
        email='admin@test.com',
        defaults={'role': 'ADMIN', 'name': 'Admin User'}
    )
    print(f"Администратор: {admin.email} ({'создан' if created else 'найден'})")
    
    # Создаем пользователя-владельца
    owner, created = User.objects.get_or_create(
        email='owner@test.com',
        defaults={'role': 'CLIENT', 'name': 'Organization Owner'}
    )
    print(f"Владелец: {owner.email} ({'создан' if created else 'найден'})")
    
    # Создаем город
    city, created = City.objects.get_or_create(
        name='Тестовый город',
        defaults={'region': 'Тестовый регион'}
    )
    
    # Создаем организацию со статусом pending
    org, created = Organization.objects.get_or_create(
        name='Новая организация',
        owner=owner,
        defaults={
            'short_name': 'НО',
            'organization_status': 'pending',
            'organization_type': 'wash',
            'city': city,
            'address': 'Тестовый адрес',
            'phone': '+79999999999',
            'email': 'org@test.com',
            'description': 'Тестовая организация на рассмотрении',
            'org_inn': '123456789012',
            'org_ogrn': '123456789012345',
            'org_kpp': '123456789'
        }
    )
    print(f"Организация: {org.name} - статус: {org.organization_status} ({'создана' if created else 'найдена'})")
    
    # Проверяем все организации по статусам
    print(f"\n=== Статистика по статусам ===")
    for status_code, status_name in Organization.STATUS_CHOICES:
        count = Organization.objects.filter(organization_status=status_code).count()
        print(f"- {status_name}: {count}")
    
    # Тестируем сериализацию
    print(f"\n=== Данные организации ===")
    serializer = OrganizationSerializer(org)
    import json
    print(json.dumps(serializer.data, indent=2, ensure_ascii=False, default=str))
    
    # Симулируем аппрув
    print(f"\n=== Симуляция аппрува ===")
    print(f"До аппрува: статус={org.organization_status}, дата_одобрения={org.organization_date_approved}")
    
    org.organization_status = 'approved'
    org.save()  # Сработает автоматическая установка даты
    
    print(f"После аппрува: статус={org.organization_status}, дата_одобрения={org.organization_date_approved}")
    
    # Проверяем обновленные данные
    serializer = OrganizationSerializer(org)
    print(f"organizationStatus: {serializer.data['organizationStatus']}")
    print(f"organizationDateApproved: {serializer.data['organizationDateApproved']}")
    
    # Тестируем отклонение
    print(f"\n=== Симуляция отклонения ===")
    org.organization_status = 'rejected'
    org.save()
    
    print(f"После отклонения: статус={org.organization_status}, дата_одобрения={org.organization_date_approved}")

if __name__ == '__main__':
    test_organization_approval()