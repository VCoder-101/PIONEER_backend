#!/usr/bin/env python
"""
Тест БАГ-010: Создание услуги пользователем с организацией
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def test_service_create():
    print_section("ТЕСТ БАГ-010: Создание услуги пользователем с организацией")
    
    # 1. Авторизация
    print("\n1. Авторизация под клиентом...")
    email = f"test_bug010_{int(time.time())}@example.com"
    
    # Отправка кода
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": email,
        "privacy_policy_accepted": True
    })
    print(f"Отправка кода: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Ошибка отправки кода: {response.json()}")
        return
    
    code = response.json().get("dev_code", "0000")
    print(f"Dev код: {code}")
    
    # Верификация
    response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": code,
            "device_id": f"test_device_bug010_{int(time.time())}",
            "name": "Test User Bug010",
            "privacy_policy_accepted": True
        }
    )
    print(f"Верификация кода: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Ошибка верификации: {response.json()}")
        return
    
    data = response.json()
    access_token = data.get("access") or data.get("jwt", {}).get("access")
    user_id = data.get('user', {}).get('id')
    
    if not access_token:
        print(f"❌ Не удалось получить access token")
        return
    
    print(f"✅ Авторизован как: {email}")
    print(f"✅ User ID: {user_id}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Создание организации
    print("\n2. Создание организации...")
    org_data = {
        "name": f"Тестовая организация Bug010 {int(time.time())}",
        "shortName": "ТО010",
        "organizationType": "wash",
        "city": 1,
        "address": "ул. Тестовая, 1",
        "phone": "+7 900 000-00-10",
        "email": f"org010_{int(time.time())}@example.com",
        "description": "Тестовая организация для Bug010",
        "orgInn": "1234567890",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789",
        "wheelDiameters": [13, 14, 15, 16]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/organizations/",
        headers=headers,
        json=org_data
    )
    print(f"Создание организации: {response.status_code}")
    
    if response.status_code not in [200, 201]:
        print(f"❌ Ошибка создания организации: {response.json()}")
        return
    
    org = response.json()
    org_id = org["id"]
    org_status = org.get("organizationStatus", org.get("organization_status"))
    org_owner = org.get("owner")
    
    print(f"✅ Организация создана")
    print(f"   ID: {org_id}")
    print(f"   Название: {org['name']}")
    print(f"   Статус: {org_status}")
    print(f"   Владелец: {org_owner}")
    
    # 3. Попытка создать услугу для неодобренной организации
    print("\n3. Попытка создать услугу для неодобренной организации...")
    service_data = {
        "organization": org_id,
        "title": "Тестовая услуга Bug010",
        "description": "Описание тестовой услуги",
        "price": "1000.00",
        "duration": 60,
        "status": "active",
        "is_active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/services/",
        headers=headers,
        json=service_data
    )
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✅ Правильно! Нельзя создать услугу для неодобренной организации")
        print(f"   Сообщение: {response.json().get('detail', 'N/A')}")
    else:
        print(f"❌ Неожиданный статус: {response.status_code}")
        print(f"   Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return
    
    # 4. Одобрение организации через админа
    print("\n4. Одобрение организации через админа...")
    
    # Используем существующего админа или создаем нового
    admin_email = f"admin_{int(time.time())}@example.com"
    
    # Сначала создаем админа через Django (если возможно) или используем существующего
    # Для теста используем фиксированный email, но с задержкой
    admin_email = "admin@example.com"
    
    # Небольшая задержка чтобы избежать rate limiting
    print("   Ожидание 2 секунды для избежания rate limiting...")
    time.sleep(2)
    
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": admin_email,
        "privacy_policy_accepted": True
    })
    
    if response.status_code != 200:
        print(f"❌ Ошибка отправки кода админу: {response.json()}")
        return
    
    admin_code = response.json().get("dev_code", "0000")
    response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": admin_email,
            "code": admin_code,
            "device_id": f"test_device_admin_{int(time.time())}",
            "name": "Admin",
            "privacy_policy_accepted": True
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка верификации админа: {response.json()}")
        return
    
    admin_data = response.json()
    admin_token = admin_data.get("access") or admin_data.get("jwt", {}).get("access")
    admin_role = admin_data.get('role') or admin_data.get('user', {}).get('role')
    
    print(f"✅ Админ авторизован, роль: {admin_role}")
    
    if admin_role != "ADMIN":
        print(f"⚠️  Пользователь {admin_email} не является админом")
        print(f"   Пропускаем одобрение организации")
        print("\n" + "="*80)
        print("ТЕСТ ЧАСТИЧНО ПРОЙДЕН ⚠️")
        print("Проверка запрета создания услуги для неодобренной организации: ✅")
        print("Проверка создания услуги для одобренной организации: ⏭️  (пропущено)")
        print("="*80)
        return
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Одобряем организацию через специальный endpoint
    response = requests.post(
        f"{BASE_URL}/api/organizations/{org_id}/approve/",
        headers=admin_headers
    )
    print(f"Одобрение организации: {response.status_code}")
    
    if response.status_code not in [200, 201]:
        print(f"❌ Ошибка одобрения: {response.json()}")
        return
    
    print("✅ Организация одобрена")
    
    # 5. Создание услуги для одобренной организации
    print("\n5. Проверка статуса организации после одобрения...")
    response = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/",
        headers=headers
    )
    
    if response.status_code == 200:
        org_check = response.json()
        org_status_after = org_check.get("organizationStatus", org_check.get("organization_status"))
        print(f"✅ Статус организации: {org_status_after}")
    else:
        print(f"❌ Не удалось проверить статус: {response.status_code}")
    
    print("\n6. Создание услуги для одобренной организации...")
    
    response = requests.post(
        f"{BASE_URL}/api/services/",
        headers=headers,
        json=service_data
    )
    print(f"Статус: {response.status_code}")
    
    if response.status_code in [200, 201]:
        service = response.json()
        print(f"✅ Услуга создана успешно!")
        print(f"   ID: {service['id']}")
        print(f"   Название: {service['title']}")
        print(f"   Цена: {service['price']}")
        print(f"   Организация: {service.get('organization_name', service['organization'])}")
        print("\n" + "="*80)
        print("ТЕСТ ПОЛНОСТЬЮ ПРОЙДЕН ✅")
        print("="*80)
    else:
        print(f"❌ Ошибка создания услуги")
        print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print("\n" + "="*80)
        print("ТЕСТ НЕ ПРОЙДЕН ❌")
        print("="*80)

if __name__ == "__main__":
    test_service_create()
