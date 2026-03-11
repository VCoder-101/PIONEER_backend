#!/usr/bin/env python
"""
Тест для проверки API организаций
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization, City
from organizations.serializers import OrganizationSerializer

def test_organization_api():
    print("=== Тестирование API организаций ===")
    
    # Создаем тестового пользователя
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'role': 'CLIENT', 'name': 'Test User'}
    )
    print(f"Пользователь: {user.email} ({'создан' if created else 'найден'})")
    
    # Создаем город
    city, created = City.objects.get_or_create(
        name='Тестовый город',
        defaults={'region': 'Тестовый регион'}
    )
    print(f"Город: {city.name} ({'создан' if created else 'найден'})")
    
    # Создаем организацию
    org, created = Organization.objects.get_or_create(
        name='TEST ORG',
        owner=user,
        defaults={
            'short_name': 'TST',
            'organization_status': 'approved',
            'organization_type': 'wash',
            'city': city,
            'address': 'Ново-Садовая улица, 200',
            'phone': '+79033093257',
            'email': 'm.romanov.biz@gmail.com',
            'description': 'sfsafsdg',
            'org_inn': '123123123534',
            'org_ogrn': '1234543521234',
            'org_kpp': '777743621',
            'count_services': 12,
            'summary_price': 12000,
            'wheel_diameters': [13, 14, 15, 16, 17, 18]
        }
    )
    print(f"Организация: {org.name} ({'создана' if created else 'найдена'})")
    
    # Тестируем сериализатор
    serializer = OrganizationSerializer(org)
    data = serializer.data
    
    print("\n=== Результат сериализации ===")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    
    # Проверяем соответствие требуемому формату
    required_fields = [
        'id', 'name', 'shortName', 'organizationStatus', 'organizationDateApproved',
        'owner', 'owner_email', 'city', 'address', 'phone', 'email', 
        'description', 'is_active', 'created_at', 'organizationType',
        'orgOgrn', 'orgInn', 'orgKpp', 'countServices', 'summaryPrice'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        print(f"\n❌ Отсутствуют поля: {missing_fields}")
    else:
        print("\n✅ Все требуемые поля присутствуют")
    
    print(f"\n=== Формат ответа для API ===")
    api_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [data]
    }
    print(json.dumps(api_response, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    test_organization_api()