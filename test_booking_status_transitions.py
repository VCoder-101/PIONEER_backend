#!/usr/bin/env python
"""
Тест переходов статусов бронирований: confirm и complete
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def test_booking_transitions():
    print_section("ТЕСТ: Переходы статусов бронирований")
    
    # 1. Создаем организацию и одобряем её
    print("\n1. Подготовка: создание и одобрение организации...")
    
    # Создаем владельца организации
    owner_email = f"owner_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": owner_email,
        "privacy_policy_accepted": True
    })
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    code = response.json().get("dev_code")
    response = requests.post(f"{BASE_URL}/api/users/auth/verify-code/", json={
        "email": owner_email,
        "code": code,
        "device_id": f"device_{int(time.time())}",
        "name": "Owner",
        "privacy_policy_accepted": True
    })
    
    owner_data = response.json()
    owner_token = owner_data.get("access") or owner_data.get("jwt", {}).get("access")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    
    # Создаем организацию
    org_data = {
        "name": f"Test Org {int(time.time())}",
        "shortName": "TO",
        "organizationType": "wash",
        "city": 1,
        "address": "Test Address",
        "phone": "+7 900 000-00-00",
        "email": f"org_{int(time.time())}@example.com",
        "orgInn": "1234567890",
        "orgOgrn": "123456789012345",
        "orgKpp": "123456789"
    }
    
    response = requests.post(f"{BASE_URL}/api/organizations/", headers=owner_headers, json=org_data)
    org = response.json()
    org_id = org["id"]
    
    # Одобряем через админа
    time.sleep(2)
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": "admin@example.com",
        "privacy_policy_accepted": True
    })
    
    if response.status_code == 200:
        admin_code = response.json().get("dev_code")
        response = requests.post(f"{BASE_URL}/api/users/auth/verify-code/", json={
            "email": "admin@example.com",
            "code": admin_code,
            "device_id": f"admin_{int(time.time())}",
            "name": "Admin",
            "privacy_policy_accepted": True
        })
        
        admin_data = response.json()
        admin_token = admin_data.get("access") or admin_data.get("jwt", {}).get("access")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        requests.post(f"{BASE_URL}/api/organizations/{org_id}/approve/", headers=admin_headers)
    
    # Создаем услугу
    service_data = {
        "organization": org_id,
        "title": "Test Service",
        "description": "Test",
        "price": "1000.00",
        "duration": 60,
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/api/services/", headers=owner_headers, json=service_data)
    service = response.json()
    service_id = service["id"]
    
    print(f"✅ Организация и услуга созданы")
    
    # 2. Создаем клиента и бронирование
    print("\n2. Создание клиента и бронирования...")
    
    client_email = f"client_{int(time.time())}@example.com"
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": client_email,
        "privacy_policy_accepted": True
    })
    
    code = response.json().get("dev_code")
    response = requests.post(f"{BASE_URL}/api/users/auth/verify-code/", json={
        "email": client_email,
        "code": code,
        "device_id": f"client_{int(time.time())}",
        "name": "Client",
        "privacy_policy_accepted": True
    })
    
    client_data = response.json()
    client_token = client_data.get("access") or client_data.get("jwt", {}).get("access")
    client_headers = {"Authorization": f"Bearer {client_token}"}
    
    # Создаем бронирование
    booking_data = {
        "service": service_id,
        "scheduled_at": "2026-03-30T10:00:00Z",
        "status": "NEW",
        "carModel": "Test Car"
    }
    
    response = requests.post(f"{BASE_URL}/api/bookings/", headers=client_headers, json=booking_data)
    booking = response.json()
    booking_id = booking["id"]
    
    print(f"✅ Бронирование создано (ID: {booking_id}, статус: {booking['status']})")
    
    # 3. Тест: подтверждение бронирования
    print("\n3. Тест: подтверждение бронирования организацией...")
    
    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/confirm/", headers=owner_headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Бронирование подтверждено")
        print(f"   Сообщение: {result['message']}")
        print(f"   Подтвердил: {result['confirmed_by']}")
        print(f"   Старый статус: {result['old_status']}")
        print(f"   Новый статус: {result['booking']['status']}")
        
        if result['booking']['status'] == 'CONFIRMED':
            print(f"   ✅ Статус корректно изменен на CONFIRMED")
        else:
            print(f"   ❌ Ошибка: ожидался CONFIRMED, получен {result['booking']['status']}")
            return
    else:
        print(f"❌ Ошибка подтверждения: {response.json()}")
        return
    
    # 4. Тест: попытка повторного подтверждения
    print("\n4. Тест: попытка повторного подтверждения...")
    
    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/confirm/", headers=owner_headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 400:
        error = response.json()
        print(f"✅ Правильно! Нельзя повторно подтвердить")
        print(f"   Сообщение: {error['error']}")
    else:
        print(f"❌ Ожидался статус 400, получен {response.status_code}")
    
    # 5. Тест: завершение бронирования
    print("\n5. Тест: завершение бронирования организацией...")
    
    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/complete/", headers=owner_headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Бронирование завершено")
        print(f"   Сообщение: {result['message']}")
        print(f"   Завершил: {result['completed_by']}")
        print(f"   Старый статус: {result['old_status']}")
        print(f"   Новый статус: {result['booking']['status']}")
        
        if result['booking']['status'] == 'DONE':
            print(f"   ✅ Статус корректно изменен на DONE")
        else:
            print(f"   ❌ Ошибка: ожидался DONE, получен {result['booking']['status']}")
            return
    else:
        print(f"❌ Ошибка завершения: {response.json()}")
        return
    
    # 6. Тест: попытка отменить завершенное бронирование
    print("\n6. Тест: попытка отменить завершенное бронирование...")
    
    response = requests.post(f"{BASE_URL}/api/bookings/{booking_id}/cancel/", headers=client_headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 400:
        error = response.json()
        print(f"✅ Правильно! Нельзя отменить завершенное бронирование")
        print(f"   Сообщение: {error['error']}")
    else:
        print(f"❌ Ожидался статус 400, получен {response.status_code}")
    
    # 7. Тест полного цикла: NEW → CONFIRMED → DONE
    print("\n7. Тест полного цикла: NEW → CONFIRMED → DONE...")
    
    # Создаем новое бронирование
    booking_data["scheduled_at"] = "2026-03-31T11:00:00Z"
    response = requests.post(f"{BASE_URL}/api/bookings/", headers=client_headers, json=booking_data)
    booking2 = response.json()
    booking2_id = booking2["id"]
    
    statuses = [booking2["status"]]
    
    # Подтверждаем
    response = requests.post(f"{BASE_URL}/api/bookings/{booking2_id}/confirm/", headers=owner_headers)
    if response.status_code == 200:
        statuses.append(response.json()['booking']['status'])
    
    # Завершаем
    response = requests.post(f"{BASE_URL}/api/bookings/{booking2_id}/complete/", headers=owner_headers)
    if response.status_code == 200:
        statuses.append(response.json()['booking']['status'])
    
    expected = ['NEW', 'CONFIRMED', 'DONE']
    if statuses == expected:
        print(f"✅ Полный цикл пройден корректно: {' → '.join(statuses)}")
    else:
        print(f"❌ Ошибка цикла: ожидалось {expected}, получено {statuses}")
        return
    
    # Итог
    print("\n" + "="*80)
    print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ ✅")
    print("="*80)
    print("\nДоступные переходы:")
    print("  NEW → CONFIRMED (confirm)")
    print("  NEW → CANCELLED (cancel)")
    print("  CONFIRMED → DONE (complete)")
    print("  CONFIRMED → CANCELLED (cancel)")

if __name__ == "__main__":
    test_booking_transitions()
