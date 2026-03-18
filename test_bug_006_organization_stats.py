"""
Тест для БАГ-006: Проверка подсчета количества и суммы услуг организации.

Проблема: Поля countServices и summaryPrice не приходят в ответе API организации.
Ожидаемое поведение: API должен возвращать актуальное количество и сумму активных услуг.
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_organization_stats():
    print("=" * 80)
    print("ТЕСТ БАГ-006: Подсчет количества и суммы услуг организации")
    print("=" * 80)
    
    # Шаг 1: Авторизация и создание организации
    print("\n1. Авторизация и создание организации...")
    email = "test_bug006_owner@example.com"
    device_id = "test-device-bug006"
    
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
            "name": "Test Owner Bug 006",
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
            "name": "Test Organization Bug 006",
            "shortName": "TO-006",
            "organizationType": "wash",
            "city": 1,
            "address": "Test Address",
            "phone": "+7 900 000-00-06",
            "email": "test-org-006@example.com",
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
    
    # Шаг 2: Проверка начальных значений
    print("\n2. Проверка начальных значений (без услуг)...")
    
    get_org_response = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if get_org_response.status_code != 200:
        print(f"   ❌ Ошибка получения организации: {get_org_response.text}")
        return
    
    org = get_org_response.json()
    
    if "countServices" not in org:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Поле countServices отсутствует")
        return
    
    if "summaryPrice" not in org:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Поле summaryPrice отсутствует")
        return
    
    print(f"   ✅ countServices: {org['countServices']}")
    print(f"   ✅ summaryPrice: {org['summaryPrice']}")
    
    if org['countServices'] != 0:
        print(f"   ⚠️  Ожидалось 0 услуг, получено {org['countServices']}")
    
    if org['summaryPrice'] != "0.00":
        print(f"   ⚠️  Ожидалась сумма 0.00, получено {org['summaryPrice']}")
    
    # Шаг 3: Создание услуг
    print("\n3. Создание услуг...")
    
    services = [
        {"title": "Service 1", "price": "1000.00", "duration": 60},
        {"title": "Service 2", "price": "1500.00", "duration": 90},
        {"title": "Service 3", "price": "2000.00", "duration": 120},
    ]
    
    created_services = []
    
    for service_data in services:
        service_response = requests.post(
            f"{BASE_URL}/api/services/",
            json={
                "organization": org_id,
                "title": service_data["title"],
                "description": f"Test service {service_data['title']}",
                "price": service_data["price"],
                "duration": service_data["duration"],
                "status": "active"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if service_response.status_code == 201:
            service = service_response.json()
            created_services.append(service)
            print(f"   ✅ Создана услуга: {service_data['title']} - {service_data['price']} руб")
        else:
            print(f"   ❌ Ошибка создания услуги: {service_response.text}")
    
    # Шаг 4: Проверка обновленных значений
    print("\n4. Проверка обновленных значений (после создания услуг)...")
    
    get_org_response2 = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if get_org_response2.status_code != 200:
        print(f"   ❌ Ошибка получения организации: {get_org_response2.text}")
        return
    
    org2 = get_org_response2.json()
    
    count_services = org2.get('countServices', 0)
    summary_price = org2.get('summaryPrice', "0.00")
    
    print(f"   countServices: {count_services}")
    print(f"   summaryPrice: {summary_price}")
    
    expected_count = len(created_services)
    expected_sum = sum(float(s["price"]) for s in services)
    
    if count_services == expected_count:
        print(f"   ✅ Количество услуг корректно: {count_services}")
    else:
        print(f"   ❌ Ожидалось {expected_count} услуг, получено {count_services}")
        return
    
    if float(summary_price) == expected_sum:
        print(f"   ✅ Сумма услуг корректна: {summary_price}")
    else:
        print(f"   ❌ Ожидалась сумма {expected_sum}, получено {summary_price}")
        return
    
    # Шаг 5: Деактивация одной услуги
    print("\n5. Деактивация одной услуги...")
    
    if created_services:
        service_to_deactivate = created_services[0]
        deactivate_response = requests.patch(
            f"{BASE_URL}/api/services/{service_to_deactivate['id']}/",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if deactivate_response.status_code == 200:
            print(f"   ✅ Услуга деактивирована: {service_to_deactivate['title']}")
        else:
            print(f"   ⚠️  Ошибка деактивации: {deactivate_response.text}")
    
    # Шаг 6: Проверка после деактивации
    print("\n6. Проверка после деактивации услуги...")
    
    get_org_response3 = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if get_org_response3.status_code != 200:
        print(f"   ❌ Ошибка получения организации: {get_org_response3.text}")
        return
    
    org3 = get_org_response3.json()
    
    count_services_after = org3.get('countServices', 0)
    summary_price_after = org3.get('summaryPrice', "0.00")
    
    print(f"   countServices: {count_services_after}")
    print(f"   summaryPrice: {summary_price_after}")
    
    expected_count_after = expected_count - 1
    expected_sum_after = expected_sum - float(services[0]["price"])
    
    if count_services_after == expected_count_after:
        print(f"   ✅ Количество активных услуг корректно: {count_services_after}")
    else:
        print(f"   ⚠️  Ожидалось {expected_count_after} услуг, получено {count_services_after}")
    
    if abs(float(summary_price_after) - expected_sum_after) < 0.01:
        print(f"   ✅ Сумма активных услуг корректна: {summary_price_after}")
    else:
        print(f"   ⚠️  Ожидалась сумма {expected_sum_after}, получено {summary_price_after}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-006 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_organization_stats()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
