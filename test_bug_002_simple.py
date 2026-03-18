"""
Упрощенный тест для БАГ-002: Создание организации клиентом.
Использует существующего пользователя из БД.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_organization_create_with_existing_user():
    print("=" * 80)
    print("ТЕСТ БАГ-002: Создание организации клиентом (упрощенный)")
    print("=" * 80)
    
    # Используем тестового пользователя
    # Если у вас есть тестовый пользователь в БД, укажите его email
    email = input("\nВведите email существующего пользователя (или нажмите Enter для создания нового): ").strip()
    
    if not email:
        print("\n⚠️  Для полного теста нужен запущенный сервер и настроенный email.")
        print("Запустите: python manage.py runserver")
        print("Затем используйте test_bug_002_organization_create.py")
        return
    
    device_id = "test-device-bug002"
    
    print(f"\n1. Отправка кода на {email}...")
    send_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={
            "email": email,
            "privacy_policy_accepted": True
        }
    )
    
    print(f"   Статус: {send_response.status_code}")
    
    if send_response.status_code != 200:
        print(f"   ❌ Ошибка: {send_response.text}")
        return
    
    response_data = send_response.json()
    print(f"   ✅ Код отправлен")
    
    # Если есть dev_code, используем его
    if "dev_code" in response_data:
        code = response_data["dev_code"]
        print(f"   Dev код: {code}")
    else:
        code = input("   Введите код из email: ").strip()
    
    print(f"\n2. Верификация кода...")
    verify_response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": code,
            "device_id": device_id,
            "privacy_policy_accepted": True
        }
    )
    
    print(f"   Статус: {verify_response.status_code}")
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    access_token = auth_data["jwt"]["access"]
    user_role = auth_data["user"]["role"]
    
    print(f"   ✅ Авторизован")
    print(f"   Роль: {user_role}")
    
    print(f"\n3. Создание организации...")
    
    org_data = {
        "name": "Тестовая Организация БАГ-002",
        "shortName": "ТО-002",
        "organizationType": "wash",
        "city": 1,
        "address": "ул. Тестовая, 1",
        "phone": "+7 900 000-00-02",
        "email": "test-org-002@example.com",
        "description": "Тестовая организация для проверки БАГ-002",
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
        org = create_response.json()
        print(f"\n   Детали:")
        print(f"   - ID: {org.get('id')}")
        print(f"   - Название: {org.get('name')}")
        print(f"   - Статус: {org.get('organizationStatus')}")
        print(f"   - Владелец: {org.get('owner_email')}")
        
        if org.get('organizationStatus') == 'pending':
            print(f"\n   ✅ Статус 'pending' установлен корректно")
        
    elif create_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        print(f"   Ответ: {create_response.text}")
        
    elif create_response.status_code == 400:
        print(f"   ⚠️  Ошибка валидации данных")
        print(f"   Ответ: {create_response.text}")
        
    else:
        print(f"   ❌ Неожиданный статус")
        print(f"   Ответ: {create_response.text}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_organization_create_with_existing_user()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
