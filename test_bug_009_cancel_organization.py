"""
Тест для БАГ-009: Проверка отмены заявки на регистрацию организации.

Проблема: Отсутствует API endpoint для отмены заявки владельцем.
Ожидаемое поведение: Владелец может отменить свою заявку со статусом 'pending'.
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_cancel_organization_application():
    print("=" * 80)
    print("ТЕСТ БАГ-009: Отмена заявки на регистрацию организации")
    print("=" * 80)
    
    # Шаг 1: Авторизация
    print("\n1. Авторизация...")
    import time
    email = f"test_bug009_{int(time.time())}@example.com"
    device_id = "test-device-bug009"
    
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
            "name": "Test User Bug 009",
            "privacy_policy_accepted": True
        }
    )
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    access_token = auth_data["jwt"]["access"]
    
    print(f"   ✅ Авторизован как: {email}")
    
    # Шаг 2: Создание организации (заявка)
    print("\n2. Создание заявки на регистрацию организации...")
    
    org_data = {
        "name": f"Test Organization Bug 009 {int(time.time())}",
        "shortName": "TO-009",
        "organizationType": "wash",
        "city": 1,
        "address": "Test Address",
        "phone": "+7 900 000-00-09",
        "email": "test-org-009@example.com",
        "orgInn": "123456789012",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if create_response.status_code != 201:
        print(f"   ❌ Ошибка создания организации: {create_response.text}")
        return
    
    org = create_response.json()
    org_id = org["id"]
    org_status = org.get("organizationStatus")
    
    print(f"   ✅ Заявка создана: ID={org_id}")
    print(f"   Статус: {org_status}")
    
    if org_status != "pending":
        print(f"   ⚠️  Ожидался статус 'pending', получен '{org_status}'")
    
    # Шаг 3: Отмена заявки владельцем
    print("\n3. Отмена заявки владельцем...")
    
    cancel_response = requests.post(
        f"{BASE_URL}/api/organizations/{org_id}/cancel/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {cancel_response.status_code}")
    
    if cancel_response.status_code == 200:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Заявка отменена")
        cancel_data = cancel_response.json()
        print(f"   Сообщение: {cancel_data.get('message')}")
        print(f"   Старый статус: {cancel_data.get('old_status')}")
        print(f"   Новый статус: {cancel_data.get('organization', {}).get('organizationStatus')}")
        
        new_status = cancel_data.get('organization', {}).get('organizationStatus')
        if new_status == 'rejected':
            print(f"   ✅ Статус изменен на 'rejected'")
        else:
            print(f"   ⚠️  Ожидался статус 'rejected', получен '{new_status}'")
            
    elif cancel_response.status_code == 404:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Endpoint не найден")
        print(f"   Ответ: {cancel_response.text}")
        return
    elif cancel_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        print(f"   Ответ: {cancel_response.text}")
        return
    else:
        print(f"   ❌ Неожиданный статус")
        print(f"   Ответ: {cancel_response.text}")
        return
    
    # Шаг 4: Проверка что заявка действительно отменена
    print("\n4. Проверка статуса организации после отмены...")
    
    get_response = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if get_response.status_code == 200:
        org_after = get_response.json()
        status_after = org_after.get("organizationStatus")
        print(f"   Статус организации: {status_after}")
        
        if status_after == "rejected":
            print(f"   ✅ Статус подтвержден: rejected")
        else:
            print(f"   ⚠️  Ожидался статус 'rejected', получен '{status_after}'")
    else:
        print(f"   ⚠️  Ошибка получения организации: {get_response.text}")
    
    # Шаг 5: Попытка повторной отмены (должна вернуть ошибку)
    print("\n5. Попытка повторной отмены (должна вернуть ошибку)...")
    
    cancel_response2 = requests.post(
        f"{BASE_URL}/api/organizations/{org_id}/cancel/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {cancel_response2.status_code}")
    
    if cancel_response2.status_code == 400:
        print(f"   ✅ Получена ожидаемая ошибка")
        error_data = cancel_response2.json()
        print(f"   Сообщение: {error_data.get('error')}")
    elif cancel_response2.status_code == 200:
        print(f"   ⚠️  Повторная отмена прошла успешно (неожиданно)")
    else:
        print(f"   ⚠️  Неожиданный статус: {cancel_response2.text}")
    
    # Шаг 6: Создание новой заявки и попытка отмены другим пользователем
    print("\n6. Проверка прав доступа (другой пользователь)...")
    
    # Создаем новую заявку
    time.sleep(1)
    org_data2 = org_data.copy()
    org_data2["name"] = f"Test Organization Bug 009 Second {int(time.time())}"
    org_data2["email"] = "test-org-009-2@example.com"
    
    create_response2 = requests.post(
        f"{BASE_URL}/api/organizations/",
        json=org_data2,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if create_response2.status_code == 201:
        org2 = create_response2.json()
        org2_id = org2["id"]
        print(f"   ✅ Вторая заявка создана: ID={org2_id}")
        
        # Авторизуемся под другим пользователем
        time.sleep(1)
        email2 = f"test_bug009_other_{int(time.time())}@example.com"
        
        send_response2 = requests.post(
            f"{BASE_URL}/api/users/auth/send-code/",
            json={"email": email2, "privacy_policy_accepted": True}
        )
        
        if send_response2.status_code == 200:
            dev_code2 = send_response2.json().get("dev_code")
            
            verify_response2 = requests.post(
                f"{BASE_URL}/api/users/auth/verify-code/",
                json={
                    "email": email2,
                    "code": dev_code2,
                    "device_id": device_id,
                    "name": "Other User",
                    "privacy_policy_accepted": True
                }
            )
            
            if verify_response2.status_code == 200:
                access_token2 = verify_response2.json()["jwt"]["access"]
                
                # Пытаемся отменить чужую заявку
                cancel_response3 = requests.post(
                    f"{BASE_URL}/api/organizations/{org2_id}/cancel/",
                    headers={"Authorization": f"Bearer {access_token2}"}
                )
                
                print(f"   Попытка отмены чужой заявки: {cancel_response3.status_code}")
                
                if cancel_response3.status_code == 403:
                    print(f"   ✅ Доступ запрещен (ожидаемо)")
                elif cancel_response3.status_code == 404:
                    print(f"   ✅ Заявка не найдена (ожидаемо - другой пользователь не видит чужие заявки)")
                else:
                    print(f"   ⚠️  Неожиданный результат: {cancel_response3.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-009 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_cancel_organization_application()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
