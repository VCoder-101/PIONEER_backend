"""
Тест для БАГ-005: Проверка permissions для редактирования услуг владельцем организации.

Проблема: Владелец организации (CLIENT с организацией) не может редактировать свои услуги.
Получает 403 Forbidden из-за проверки несуществующей роли ORGANIZATION.

Ожидаемое поведение: Владелец организации может создавать и редактировать услуги своей организации.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_service_owner_can_edit():
    print("=" * 80)
    print("ТЕСТ БАГ-005: Редактирование услуг владельцем организации")
    print("=" * 80)
    
    # Шаг 1: Авторизация и создание организации
    print("\n1. Авторизация и создание организации...")
    email = "test_bug005_owner@example.com"
    device_id = "test-device-bug005"
    
    send_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": email, "privacy_policy_accepted": True}
    )
    
    if send_response.status_code != 200:
        print(f"   ❌ Ошибка отправки кода: {send_response.text}")
        return
    
    dev_code = send_response.json().get("dev_code")
    
    verify_response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": dev_code,
            "device_id": device_id,
            "name": "Test Owner Bug 005",
            "privacy_policy_accepted": True
        }
    )
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    access_token = auth_data["jwt"]["access"]
    
    print(f"   ✅ Авторизован как: {email}")
    
    # Создаем организацию
    org_response = requests.post(
        f"{BASE_URL}/api/organizations/",
        json={
            "name": "Test Organization Bug 005",
            "shortName": "TO-005",
            "organizationType": "wash",
            "city": 1,
            "address": "Test Address",
            "phone": "+7 900 000-00-05",
            "email": "test-org-005@example.com",
            "orgInn": "123456789012",
            "orgOgrn": "123456789012345",
            "orgKpp": "123456789"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if org_response.status_code != 201:
        print(f"   ❌ Ошибка создания организации: {org_response.text}")
        return
    
    org_data = org_response.json()
    org_id = org_data["id"]
    print(f"   ✅ Организация создана: ID={org_id}")
    
    # Шаг 2: Создание услуги
    print("\n2. Создание услуги...")
    
    service_data = {
        "organization": org_id,
        "title": "Test Service Bug 005",
        "description": "Test service for bug 005",
        "price": "1000.00",
        "duration": 60,
        "status": "active"
    }
    
    create_service_response = requests.post(
        f"{BASE_URL}/api/services/",
        json=service_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {create_service_response.status_code}")
    
    if create_service_response.status_code == 201:
        print(f"   ✅ Услуга создана")
        service = create_service_response.json()
        service_id = service["id"]
        print(f"   ID услуги: {service_id}")
    elif create_service_response.status_code == 403:
        print(f"   ❌ Доступ запрещен при создании услуги")
        print(f"   Ответ: {create_service_response.text}")
        return
    else:
        print(f"   ❌ Ошибка: {create_service_response.text}")
        return
    
    # Шаг 3: Редактирование услуги
    print("\n3. Редактирование услуги...")
    
    update_data = {
        "title": "Updated Service Bug 005",
        "price": "1500.00"
    }
    
    update_response = requests.patch(
        f"{BASE_URL}/api/services/{service_id}/",  # С trailing slash!
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {update_response.status_code}")
    
    if update_response.status_code == 200:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Услуга обновлена")
        updated_service = update_response.json()
        print(f"   Новое название: {updated_service.get('title')}")
        print(f"   Новая цена: {updated_service.get('price')}")
    elif update_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        print(f"   Ответ: {update_response.text}")
        return
    else:
        print(f"   ❌ Неожиданный статус")
        print(f"   Ответ: {update_response.text}")
        return
    
    # Шаг 4: Проверка что услуга видна владельцу
    print("\n4. Проверка видимости услуги...")
    
    list_response = requests.get(
        f"{BASE_URL}/api/services/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if list_response.status_code == 200:
        services = list_response.json()
        if isinstance(services, list):
            service_count = len(services)
        else:
            service_count = services.get('count', 0)
        
        print(f"   ✅ Получено услуг: {service_count}")
    else:
        print(f"   ⚠️  Ошибка получения списка: {list_response.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-005 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_service_owner_can_edit()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
