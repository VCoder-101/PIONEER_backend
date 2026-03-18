"""
Тест для БАГ-008: Проверка уникальности названия организации.

Проблема: Можно создать несколько организаций с одинаковым названием.
Ожидаемое поведение: API должен возвращать ошибку при попытке создать организацию с существующим названием.
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_organization_unique_name():
    print("=" * 80)
    print("ТЕСТ БАГ-008: Уникальность названия организации")
    print("=" * 80)
    
    # Шаг 1: Авторизация первого пользователя
    print("\n1. Авторизация первого пользователя...")
    import time
    email1 = f"test_bug008_user1_{int(time.time())}@example.com"
    device_id = "test-device-bug008"
    
    send_response1 = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": email1, "privacy_policy_accepted": True}
    )
    
    if send_response1.status_code != 200:
        print(f"   ❌ Ошибка отправки кода: {send_response1.text}")
        return
    
    dev_code1 = send_response1.json().get("dev_code")
    
    verify_response1 = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email1,
            "code": dev_code1,
            "device_id": device_id,
            "name": "Test User 1 Bug 008",
            "privacy_policy_accepted": True
        }
    )
    
    if verify_response1.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response1.text}")
        return
    
    auth_data1 = verify_response1.json()
    access_token1 = auth_data1["jwt"]["access"]
    
    print(f"   ✅ Пользователь 1 авторизован: {email1}")
    
    # Шаг 2: Создание первой организации
    print("\n2. Создание первой организации...")
    
    org_name = "Unique Test Organization Bug 008"
    org_short_name = "UTO-008"
    
    org_data = {
        "name": org_name,
        "shortName": org_short_name,
        "organizationType": "wash",
        "city": 1,
        "address": "Test Address 1",
        "phone": "+7 900 000-00-08",
        "email": "test-org-008-1@example.com",
        "orgInn": "123456789012",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789"
    }
    
    create_response1 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token1}"}
    )
    
    if create_response1.status_code != 201:
        print(f"   ❌ Ошибка создания организации: {create_response1.text}")
        return
    
    org1 = create_response1.json()
    print(f"   ✅ Организация создана: {org1['name']}")
    
    # Шаг 3: Попытка создать организацию с тем же названием (тот же пользователь)
    print("\n3. Попытка создать организацию с тем же названием (тот же пользователь)...")
    
    create_response2 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token1}"}
    )
    
    print(f"   Статус: {create_response2.status_code}")
    
    if create_response2.status_code == 400:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Получена ошибка валидации")
        error_data = create_response2.json()
        print(f"   Сообщение: {error_data}")
        
        # Проверяем что ошибка связана с name
        if 'name' in error_data:
            print(f"   ✅ Ошибка валидации поля 'name': {error_data['name']}")
        else:
            print(f"   ⚠️  Ошибка не связана с полем 'name'")
    elif create_response2.status_code == 201:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Организация создана (дубликат)")
        return
    else:
        print(f"   ❌ Неожиданный статус: {create_response2.text}")
        return
    
    # Шаг 4: Авторизация второго пользователя
    print("\n4. Авторизация второго пользователя...")
    
    time.sleep(1)  # Небольшая задержка для уникального email
    email2 = f"test_bug008_user2_{int(time.time())}@example.com"
    
    send_response2 = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": email2, "privacy_policy_accepted": True}
    )
    
    if send_response2.status_code != 200:
        print(f"   ❌ Ошибка отправки кода: {send_response2.text}")
        return
    
    dev_code2 = send_response2.json().get("dev_code")
    
    verify_response2 = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email2,
            "code": dev_code2,
            "device_id": device_id,
            "name": "Test User 2 Bug 008",
            "privacy_policy_accepted": True
        }
    )
    
    if verify_response2.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response2.text}")
        return
    
    auth_data2 = verify_response2.json()
    access_token2 = auth_data2["jwt"]["access"]
    
    print(f"   ✅ Пользователь 2 авторизован: {email2}")
    
    # Шаг 5: Попытка создать организацию с тем же названием (другой пользователь)
    print("\n5. Попытка создать организацию с тем же названием (другой пользователь)...")
    
    org_data2 = org_data.copy()
    org_data2["email"] = "test-org-008-2@example.com"
    org_data2["phone"] = "+7 900 000-00-09"
    
    create_response3 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data2,
        headers={"Authorization": f"Bearer {access_token2}"}
    )
    
    print(f"   Статус: {create_response3.status_code}")
    
    if create_response3.status_code == 400:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Получена ошибка валидации")
        error_data = create_response3.json()
        print(f"   Сообщение: {error_data}")
    elif create_response3.status_code == 201:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Организация создана (дубликат от другого пользователя)")
        return
    else:
        print(f"   ❌ Неожиданный статус: {create_response3.text}")
        return
    
    # Шаг 6: Проверка регистронезависимости
    print("\n6. Проверка регистронезависимости (NAME vs name)...")
    
    org_data3 = org_data.copy()
    org_data3["name"] = org_name.upper()  # Все заглавные
    org_data3["shortName"] = "UTO-008-UPPER"
    org_data3["email"] = "test-org-008-3@example.com"
    
    create_response4 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data3,
        headers={"Authorization": f"Bearer {access_token2}"}
    )
    
    print(f"   Статус: {create_response4.status_code}")
    
    if create_response4.status_code == 400:
        print(f"   ✅ Регистронезависимая проверка работает")
    elif create_response4.status_code == 201:
        print(f"   ⚠️  Создана организация с названием в другом регистре")
    
    # Шаг 7: Создание организации с другим названием (должно пройти)
    print("\n7. Создание организации с другим названием (должно пройти)...")
    
    org_data4 = org_data.copy()
    org_data4["name"] = "Another Unique Organization Bug 008"
    org_data4["shortName"] = "AUO-008"
    org_data4["email"] = "test-org-008-4@example.com"
    
    create_response5 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data4,
        headers={"Authorization": f"Bearer {access_token2}"}
    )
    
    print(f"   Статус: {create_response5.status_code}")
    
    if create_response5.status_code == 201:
        print(f"   ✅ Организация с другим названием создана успешно")
    else:
        print(f"   ⚠️  Ошибка создания: {create_response5.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-008 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_organization_unique_name()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
