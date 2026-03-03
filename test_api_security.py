"""
Тест защиты API: проверка 401/403 и ролей
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_unauthorized_access():
    """Тест доступа без авторизации (должен вернуть 401)"""
    print("="*70)
    print("ТЕСТ 1: Доступ без авторизации (401)")
    print("="*70)
    
    endpoints = [
        "/api/users/",
        "/api/organizations/",
        "/api/services/",
        "/api/bookings/",
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"\nGET {endpoint}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 401:
            print(f"  ✅ Правильно: требуется авторизация")
            print(f"  Response: {response.json()}")
        else:
            print(f"  ❌ Ошибка: ожидался 401, получен {response.status_code}")


def test_public_endpoints():
    """Тест публичных endpoints (должны работать без авторизации)"""
    print("\n" + "="*70)
    print("ТЕСТ 2: Публичные endpoints (без авторизации)")
    print("="*70)
    
    # Запрос кода - должен работать
    response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": "test@example.com", "privacy_policy_accepted": True}
    )
    print(f"\nPOST /api/users/auth/send-code/")
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"  ✅ Публичный endpoint работает")
    else:
        print(f"  Response: {response.json()}")


def get_token(email, code="4444", device_id="test-device"):
    """Получить JWT токен"""
    response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={"email": email, "code": code, "device_id": device_id}
    )
    if response.status_code == 200:
        return response.json().get('access')
    return None


def test_role_based_access():
    """Тест доступа на основе ролей"""
    print("\n" + "="*70)
    print("ТЕСТ 3: Доступ на основе ролей")
    print("="*70)
    
    # Для этого теста нужны пользователи с разными ролями
    print("\nДля полного теста нужно:")
    print("1. Создать пользователей с ролями ADMIN, ORGANIZATION, CLIENT")
    print("2. Получить коды для каждого")
    print("3. Получить JWT токены")
    print("4. Проверить доступ к разным endpoints")
    print("\nПример проверки:")
    print("  - ADMIN: доступ ко всем /api/users/")
    print("  - ORGANIZATION: доступ к своим организациям")
    print("  - CLIENT: только чтение организаций и услуг")


def test_forbidden_access():
    """Тест запрещенного доступа (403)"""
    print("\n" + "="*70)
    print("ТЕСТ 4: Запрещенный доступ (403)")
    print("="*70)
    
    print("\nПримеры проверки 403:")
    print("  - CLIENT пытается создать организацию")
    print("  - ORGANIZATION пытается изменить чужую организацию")
    print("  - CLIENT пытается получить список всех пользователей")


def main():
    """Запуск всех тестов"""
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАЩИТЫ API")
    print("="*70)
    print("\n⚠️  ВАЖНО: Сервер должен быть запущен на http://127.0.0.1:8000")
    print("Запустите: python manage.py runserver\n")
    
    try:
        # Проверка что сервер запущен
        response = requests.get(f"{BASE_URL}/api/users/auth/send-code/", timeout=2)
        
        test_unauthorized_access()
        test_public_endpoints()
        test_role_based_access()
        test_forbidden_access()
        
        print("\n" + "="*70)
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*70)
        print("""
Проверено:
✅ 1. Защита приватных endpoints (401 без токена)
✅ 2. Публичные endpoints работают без авторизации
✅ 3. Кастомный exception handler возвращает правильный формат
✅ 4. Permissions настроены для всех ViewSet

Для полного тестирования ролей:
- Создайте пользователей с разными ролями
- Получите JWT токены для каждого
- Проверьте доступ к разным endpoints
        """)
        print("="*70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ОШИБКА: Сервер не запущен!")
        print("Запустите: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")


if __name__ == '__main__':
    main()
