#!/usr/bin/env python
"""
Тест БАГ-011: Полная проверка статусов бронирования в календаре
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def test_calendar_statuses():
    print_section("ТЕСТ БАГ-011: Проверка всех статусов в календаре")
    
    # 1. Авторизация
    print("\n1. Авторизация под клиентом...")
    email = f"test_bug011_full_{int(time.time())}@example.com"
    
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": email,
        "privacy_policy_accepted": True
    })
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    code = response.json().get("dev_code", "0000")
    
    response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": code,
            "device_id": f"test_device_{int(time.time())}",
            "name": "Test User",
            "privacy_policy_accepted": True
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    data = response.json()
    access_token = data.get("access") or data.get("jwt", {}).get("access")
    print(f"✅ Авторизован")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Получаем услугу
    print("\n2. Получение услуги...")
    response = requests.get(f"{BASE_URL}/api/services/", headers=headers)
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    services_data = response.json()
    services = services_data.get("results", []) if isinstance(services_data, dict) else services_data
    
    if not services:
        print("❌ Нет доступных услуг")
        return
    
    service_id = services[0]["id"]
    print(f"✅ Используем услугу ID: {service_id}")
    
    # 3. Создаем бронирования с разными статусами
    print("\n3. Создание тестовых бронирований...")
    
    bookings_created = []
    
    # Создаем NEW бронирование
    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        headers=headers,
        json={
            "service": service_id,
            "scheduled_at": "2026-03-25T10:00:00Z",
            "status": "NEW",
            "carModel": "Test Car NEW"
        }
    )
    if response.status_code in [200, 201]:
        booking = response.json()
        bookings_created.append(("NEW", booking["id"]))
        print(f"✅ Создано бронирование NEW (ID: {booking['id']})")
    
    # Создаем CONFIRMED бронирование
    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        headers=headers,
        json={
            "service": service_id,
            "scheduled_at": "2026-03-26T11:00:00Z",
            "status": "CONFIRMED",
            "carModel": "Test Car CONFIRMED"
        }
    )
    if response.status_code in [200, 201]:
        booking = response.json()
        bookings_created.append(("CONFIRMED", booking["id"]))
        print(f"✅ Создано бронирование CONFIRMED (ID: {booking['id']})")
    
    # Создаем бронирование и отменяем его
    response = requests.post(
        f"{BASE_URL}/api/bookings/",
        headers=headers,
        json={
            "service": service_id,
            "scheduled_at": "2026-03-27T12:00:00Z",
            "status": "NEW",
            "carModel": "Test Car CANCELLED"
        }
    )
    if response.status_code in [200, 201]:
        booking = response.json()
        booking_id = booking["id"]
        
        # Отменяем
        response = requests.post(
            f"{BASE_URL}/api/bookings/{booking_id}/cancel/",
            headers=headers
        )
        if response.status_code == 200:
            bookings_created.append(("CANCELLED", booking_id))
            print(f"✅ Создано и отменено бронирование CANCELLED (ID: {booking_id})")
    
    # 4. Проверяем календарь
    print("\n4. Проверка календаря...")
    response = requests.get(f"{BASE_URL}/api/bookings/calendar/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.json()}")
        return
    
    calendar_data = response.json()
    bookings = calendar_data.get("results", []) if isinstance(calendar_data, dict) else calendar_data
    
    print(f"✅ Получено бронирований в календаре: {len(bookings)}")
    
    # 5. Проверяем каждое бронирование
    print("\n5. Проверка статусов...")
    
    test_results = []
    
    for expected_status, booking_id in bookings_created:
        # Находим бронирование в календаре
        booking = next((b for b in bookings if b["id"] == booking_id), None)
        
        if not booking:
            print(f"❌ Бронирование {booking_id} не найдено в календаре")
            test_results.append(False)
            continue
        
        status = booking.get("status")
        booking_status = booking.get("bookingStatus")
        
        # Определяем ожидаемый bookingStatus
        expected_booking_status = "active" if expected_status in ["NEW", "CONFIRMED"] else "archived"
        
        status_ok = status == expected_status
        booking_status_ok = booking_status == expected_booking_status
        
        result = "✅" if (status_ok and booking_status_ok) else "❌"
        
        print(f"{result} ID {booking_id}:")
        print(f"   status: {status} (ожидалось: {expected_status}) {'✅' if status_ok else '❌'}")
        print(f"   bookingStatus: {booking_status} (ожидалось: {expected_booking_status}) {'✅' if booking_status_ok else '❌'}")
        
        test_results.append(status_ok and booking_status_ok)
    
    # 6. Итог
    print("\n" + "="*80)
    if all(test_results):
        print("ТЕСТ ПОЛНОСТЬЮ ПРОЙДЕН ✅")
        print("Все статусы бронирований корректно отображаются в календаре:")
        print("  - NEW → bookingStatus: active ✅")
        print("  - CONFIRMED → bookingStatus: active ✅")
        print("  - CANCELLED → bookingStatus: archived ✅")
    else:
        print("ТЕСТ НЕ ПРОЙДЕН ❌")
        print(f"Успешно: {sum(test_results)}/{len(test_results)}")
    print("="*80)

if __name__ == "__main__":
    test_calendar_statuses()
