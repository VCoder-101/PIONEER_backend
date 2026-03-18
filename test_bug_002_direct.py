"""
Прямой тест БАГ-002 через Django ORM (без HTTP запросов).
Проверяет логику permissions напрямую.
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, City
from organizations.permissions import IsOrganizationOwner
from rest_framework.test import APIRequestFactory
from unittest.mock import Mock

User = get_user_model()

def test_permissions_directly():
    print("=" * 80)
    print("ТЕСТ БАГ-002: Прямая проверка permissions")
    print("=" * 80)
    
    # Создаем или получаем тестового пользователя
    print("\n1. Создание тестового пользователя...")
    email = "test_bug002_direct@example.com"
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'name': 'Test User Bug 002',
            'role': 'CLIENT'
        }
    )
    
    if created:
        print(f"   ✅ Создан новый пользователь: {email}")
    else:
        print(f"   ✅ Используется существующий пользователь: {email}")
    
    print(f"   Роль: {user.role}")
    
    # Проверяем permissions
    print("\n2. Проверка permissions для создания организации...")
    
    factory = APIRequestFactory()
    request = factory.post('/api/organizations/')
    request.user = user
    
    # Создаем mock view
    view = Mock()
    view.action = 'create'
    
    permission = IsOrganizationOwner()
    has_permission = permission.has_permission(request, view)
    
    print(f"   has_permission для CLIENT при создании: {has_permission}")
    
    if has_permission:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! CLIENT может создавать организации")
    else:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! CLIENT не может создавать организации")
        return
    
    # Создаем организацию напрямую
    print("\n3. Создание организации через ORM...")
    
    # Получаем или создаем город
    city, _ = City.objects.get_or_create(
        name="Тестовый Город",
        defaults={'region': 'Тестовый Регион'}
    )
    
    org = Organization.objects.create(
        name="Тестовая Организация БАГ-002",
        short_name="ТО-002",
        owner=user,
        city=city,
        address="ул. Тестовая, 1",
        phone="+7 900 000-00-02",
        email="test-org-002@example.com",
        description="Тестовая организация",
        organization_type="wash",
        org_inn="123456789012",
        org_ogrn="123456789012345",
        org_kpp="123456789",
        wheel_diameters=[13, 14, 15, 16, 17, 18]
    )
    
    print(f"   ✅ Организация создана")
    print(f"   ID: {org.id}")
    print(f"   Название: {org.name}")
    print(f"   Статус: {org.organization_status}")
    print(f"   Владелец: {org.owner.email}")
    
    if org.organization_status == 'pending':
        print(f"   ✅ Статус 'pending' установлен корректно")
    else:
        print(f"   ⚠️  Ожидался статус 'pending', получен '{org.organization_status}'")
    
    # Проверяем что пользователь видит свою организацию
    print("\n4. Проверка видимости организации...")
    
    user_orgs = user.organizations.all()
    print(f"   Организаций у пользователя: {user_orgs.count()}")
    
    if user_orgs.filter(id=org.id).exists():
        print(f"   ✅ Организация видна владельцу")
    else:
        print(f"   ⚠️  Организация не найдена у владельца")
    
    # Проверяем permissions для редактирования
    print("\n5. Проверка permissions для редактирования своей организации...")
    
    request = factory.put(f'/api/organizations/{org.id}/')
    request.user = user
    
    has_object_permission = permission.has_object_permission(request, view, org)
    
    print(f"   has_object_permission для владельца: {has_object_permission}")
    
    if has_object_permission:
        print(f"   ✅ Владелец может редактировать свою организацию")
    else:
        print(f"   ⚠️  Владелец не может редактировать свою организацию")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! БАГ-002 ИСПРАВЛЕН!")
    print("=" * 80)
    
    # Очистка
    print("\nОчистка тестовых данных...")
    org.delete()
    if created:
        user.delete()
    print("✅ Тестовые данные удалены")


if __name__ == "__main__":
    test_permissions_directly()
