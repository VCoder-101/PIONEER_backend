#!/usr/bin/env python
"""
Тест новых API endpoints для аппрува организаций
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization
from organizations.views import OrganizationViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

def test_organization_api_endpoints():
    print("=== Тест API endpoints для аппрува ===")
    
    # Создаем factory для запросов
    factory = APIRequestFactory()
    
    # Находим администратора и организацию
    admin = User.objects.filter(role='ADMIN').first()
    org = Organization.objects.filter(organization_status='pending').first()
    
    if not admin:
        print("Нет администратора для тестирования")
        return
    
    if not org:
        # Создаем организацию для тестирования
        owner = User.objects.filter(role='CLIENT').first()
        if owner:
            org = Organization.objects.create(
                name='Тестовая организация для API',
                owner=owner,
                organization_status='pending',
                organization_type='wash'
            )
    
    if not org:
        print("Нет организации для тестирования")
        return
    
    print(f"Тестируем с администратором: {admin.email}")
    print(f"Тестируем организацию: {org.name} (статус: {org.organization_status})")
    
    # Создаем viewset
    viewset = OrganizationViewSet()
    
    # Тест 1: Получение заявок на рассмотрении
    print(f"\n=== Тест 1: Получение pending заявок ===")
    request = factory.get('/api/organizations/pending/')
    request.user = admin
    viewset.request = Request(request)
    viewset.format_kwarg = None
    
    try:
        response = viewset.pending(request)
        print(f"Статус ответа: {response.status_code}")
        print(f"Количество pending заявок: {response.data.get('count', 0)}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Тест 2: Аппрув организации
    print(f"\n=== Тест 2: Аппрув организации ===")
    request = factory.post(f'/api/organizations/{org.id}/approve/')
    request.user = admin
    viewset.request = Request(request)
    viewset.kwargs = {'pk': org.id}
    
    try:
        response = viewset.approve(request, pk=org.id)
        print(f"Статус ответа: {response.status_code}")
        print(f"Сообщение: {response.data.get('message')}")
        
        # Проверяем изменение статуса
        org.refresh_from_db()
        print(f"Новый статус организации: {org.organization_status}")
        print(f"Дата одобрения: {org.organization_date_approved}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Тест 3: Отклонение организации
    print(f"\n=== Тест 3: Отклонение организации ===")
    request = factory.post(f'/api/organizations/{org.id}/reject/')
    request.user = admin
    viewset.request = Request(request)
    viewset.kwargs = {'pk': org.id}
    
    try:
        response = viewset.reject(request, pk=org.id)
        print(f"Статус ответа: {response.status_code}")
        print(f"Сообщение: {response.data.get('message')}")
        
        # Проверяем изменение статуса
        org.refresh_from_db()
        print(f"Новый статус организации: {org.organization_status}")
        print(f"Дата одобрения: {org.organization_date_approved}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # Тест 4: Попытка аппрува не-администратором
    print(f"\n=== Тест 4: Попытка аппрува клиентом ===")
    client = User.objects.filter(role='CLIENT').first()
    if client:
        request = factory.post(f'/api/organizations/{org.id}/approve/')
        request.user = client
        viewset.request = Request(request)
        
        try:
            response = viewset.approve(request, pk=org.id)
            print(f"Статус ответа: {response.status_code}")
            print(f"Ошибка: {response.data.get('error')}")
        except Exception as e:
            print(f"Ошибка: {e}")
    
    print(f"\n=== Итоговая статистика ===")
    for status_code, status_name in Organization.STATUS_CHOICES:
        count = Organization.objects.filter(organization_status=status_code).count()
        print(f"- {status_name}: {count}")

if __name__ == '__main__':
    test_organization_api_endpoints()