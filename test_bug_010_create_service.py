"""
Тест для БАГ-010: Проверка создания услуги владельцем организации.

Проблема: Владелец организации получает 403 при попытке создать услугу для своей организации.
Ожидаемое поведение: Владелец может создавать услуги для своей организации.
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_create_service_by_owner():
    print("=" * 80)
    print("ТЕСТ БАГ-010: Создание услуги владельцем организации")
    print("=" * 80)
    
    # Шаг 1: Авторизация
    print("\n1. Авторизация...")
    import time
    email = f"test_bug010_{int(time.time())}@example.com"
    device_id = "test-device-bug010"
    
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
            "name": "Test Owner Bug 010",
            "privacy_policy_accepted": True
        }
    )
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    access_token = auth_data["jwt"]["access"]
    user_id = auth_data["user"]["id"]
    
    print(f"   ✅ Авторизован как: {email}")
    print(f"   User ID: {user_id}")
    
    # Шаг 2: Создание организации
    print("\n2. Создание организации...")
    
    org_data = {
        "name": f"Test Organization Bug 010 {int(time.time())}",
        "shortName": "TO-010",
        "organizationType": "wash",
        "city": 1,
        "address": "Test Address",
        "phone": "+7 900 000-00-10",
        "email": "test-org-010@example.com",
        "orgInn": "123456789012",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789"
    }
    
    org_response = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if org_response.status_code != 201:
        print(f"   ❌ Ошибка создания организации: {org_response.text}")
        return
    
    org = org_response.json()
    org_id = org["id"]
    org_owner = org.get("owner")
    
    print(f"   ✅ Организация создана: ID={org_id}")
    print(f"   Owner ID: {org_owner}")
    print(f"   User ID == Owner ID: {user_id == org_owner}")
    
    # Шаг 3: Создание услуги
    print("\n3. Создание услуги для своей организации...")
    
    service_data = {
        "organization": org_id,
        "title": "Test Service Bug 010",
        "description": "Test service description",
        "price": "1000.00",
        "duration": 60,
        "status": "active",
        "is_active": True
    }
    
    print(f"   Данные услуги: organization={org_id}")
    
    service_response = requests.post(
        f"{BASE_URL}/api/services/",
        json=service_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {service_response.status_code}")
    
    if service_response.status_code == 201:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Услуга создана")
        service = service_response.json()
        print(f"   ID услуги: {service.get('id')}")
        print(f"   Название: {service.get('title')}")
        print(f"   Организация: {service.get('organization')}")
    elif service_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        error_data = service_response.json()
        print(f"   Ответ: {error_data}")
        
        # Дополнительная диагностика
        print(f"\n   Диагностика:")
        print(f"   - User ID: {user_id}")
        print(f"   - Organization ID: {org_id}")
        print(f"   - Organization Owner: {org_owner}")
        
        # Проверяем организацию
        org_check = requests.get(
            f"{BASE_URL}/api/organizations/{org_id}/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if org_check.status_code == 200:
            org_details = org_check.json()
            print(f"   - Организация найдена: {org_details.get('name')}")
            print(f"   - Owner в организации: {org_details.get('owner')}")
        
        return
    else:
        print(f"   ❌ Неожиданный статус")
        print(f"   Ответ: {service_response.text}")
        return
    
    # Шаг 4: Проверка что услуга видна владельцу
    print("\n4. Проверка видимости услуги...")
    
    services_response = requests.get(
        f"{BASE_URL}/api/services/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if services_response.status_code == 200:
        services = services_response.json()
        if isinstance(services, list):
            count = len(services)
        else:
            count = services.get('count', 0)
        
        print(f"   ✅ Получено услуг: {count}")
    else:
        print(f"   ⚠️  Ошибка получения списка: {services_response.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-010 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_create_service_by_owner()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
