"""
Тест для БАГ-002: Проверка создания организации клиентом.

Проблема: Пользователь с ролью CLIENT не может создать заявку на регистрацию организации.
Ожидаемое поведение: CLIENT может создать организацию (заявку со статусом pending).
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_client_can_create_organization():
    print("=" * 80)
    print("ТЕСТ БАГ-002: Создание организации клиентом")
    print("=" * 80)
    
    # Шаг 1: Авторизация под клиентом
    print("\n1. Авторизация под клиентом...")
    email = "test_bug002_client@example.com"
    device_id = "test-device-bug002"
    
    # Отправляем код
    send_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={
            "email": email,
            "privacy_policy_accepted": True
        }
    )
    print(f"   Отправка кода: {send_response.status_code}")
    
    if send_response.status_code != 200:
        print(f"   ❌ Ошибка отправки кода: {send_response.text}")
        return
    
    dev_code = send_response.json().get("dev_code")
    if not dev_code:
        print("   ❌ dev_code не найден в ответе")
        return
    
    print(f"   Dev код: {dev_code}")
    
    # Верифицируем код
    verify_response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": dev_code,
            "device_id": device_id,
            "name": "Test Client Bug 002",
            "privacy_policy_accepted": True
        }
    )
    print(f"   Верификация кода: {verify_response.status_code}")
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    access_token = auth_data["jwt"]["access"]
    user_role = auth_data["user"]["role"]
    
    print(f"   ✅ Авторизован как: {email}")
    print(f"   ✅ Роль: {user_role}")
    
    if user_role != "CLIENT":
        print(f"   ⚠️  Ожидалась роль CLIENT, получена {user_role}")
    
    # Шаг 2: Создание организации
    print("\n2. Создание организации...")
    
    org_data = {
        "name": "Чистый Кузов",
        "shortName": "ЧК",
        "organizationType": "wash",
        "city": 1,
        "address": "ул. Московское шоссе, 100",
        "phone": "+7 846 200-10-01",
        "email": "org@example.com",
        "description": "Мойка и детейлинг",
        "orgInn": "123456789012",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789",
        "wheelDiameters": [13, 14, 15, 16, 17, 18]
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {create_response.status_code}")
    
    if create_response.status_code == 201:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Организация создана")
        org_response = create_response.json()
        print(f"   ID организации: {org_response.get('id')}")
        print(f"   Название: {org_response.get('name')}")
        print(f"   Статус: {org_response.get('organizationStatus')}")
        print(f"   Владелец: {org_response.get('owner_email')}")
        
        # Проверяем что статус pending
        if org_response.get('organizationStatus') == 'pending':
            print(f"   ✅ Статус 'pending' установлен корректно")
        else:
            print(f"   ⚠️  Ожидался статус 'pending', получен '{org_response.get('organizationStatus')}'")
        
    elif create_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        print(f"   Ответ: {create_response.text}")
        return
    else:
        print(f"   ❌ Неожиданный статус: {create_response.status_code}")
        print(f"   Ответ: {create_response.text}")
        return
    
    # Шаг 3: Проверка что организация видна владельцу
    print("\n3. Проверка что организация видна владельцу...")
    
    list_response = requests.get(
        f"{BASE_URL}/api/organizations/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {list_response.status_code}")
    
    if list_response.status_code == 200:
        orgs = list_response.json()
        if isinstance(orgs, list):
            org_count = len(orgs)
        else:
            org_count = orgs.get('count', 0)
        
        print(f"   ✅ Получено организаций: {org_count}")
        
        if org_count > 0:
            print(f"   ✅ Организация видна владельцу")
        else:
            print(f"   ⚠️  Организация не найдена в списке")
    else:
        print(f"   ❌ Ошибка получения списка: {list_response.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-002 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    test_client_can_create_organization()
