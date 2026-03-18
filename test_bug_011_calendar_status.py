#!/usr/bin/env python
"""
Тест БАГ-011: Календарь не возвращает статус бронирования (active/archived)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def test_calendar_status():
    print_section("ТЕСТ БАГ-011: Статус бронирования в календаре")
    
    # 1. Авторизация
    print("\n1. Авторизация под клиентом...")
    email = f"test_bug011_{int(time.time())}@example.com"
    
    response = requests.post(f"{BASE_URL}/api/users/auth/send-code/", json={
        "email": email,
        "privacy_policy_accepted": True
    })
    
    if response.status_code != 200:
        print(f"❌ Ошибка отправки кода: {response.json()}")
        return
    
    code = response.json().get("dev_code", "0000")
    
    response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": code,
            "device_id": f"test_device_bug011_{int(time.time())}",
            "name": "Test User Bug011",
            "privacy_policy_accepted": True
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка верификации: {response.json()}")
        return
    
    data = response.json()
    access_token = data.get("access") or data.get("jwt", {}).get("access")
    
    if not access_token:
        print(f"❌ Не удалось получить access token")
        return
    
    print(f"✅ Авторизован как: {email}")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Получение календаря
    print("\n2. Получение календаря бронирований...")
    response = requests.get(f"{BASE_URL}/api/bookings/calendar/", headers=headers)
    print(f"Статус: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения календаря: {response.json()}")
        return
    
    calendar_data = response.json()
    
    # Проверяем формат ответа
    if isinstance(calendar_data, dict):
        bookings = calendar_data.get("results", [])
    else:
        bookings = calendar_data
    
    print(f"✅ Получено бронирований: {len(bookings)}")
    
    # 3. Проверка наличия поля bookingStatus
    print("\n3. Проверка полей в ответе...")
    
    if len(bookings) == 0:
        print("⚠️  Нет бронирований для проверки")
        print("   Создадим тестовое бронирование...")
        
        # Получаем список услуг
        response = requests.get(f"{BASE_URL}/api/services/", headers=headers)
        if response.status_code == 200:
            services_data = response.json()
            if isinstance(services_data, dict):
                services = services_data.get("results", [])
            else:
                services = services_data
            
            if services:
                service_id = services[0]["id"]
                
                # Создаем бронирование
                booking_data = {
                    "service": service_id,
                    "scheduled_at": "2026-03-25T10:00:00Z",
                    "status": "NEW",
                    "carModel": "Test Car",
                    "wheelDiameter": 16
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/bookings/",
                    headers=headers,
                    json=booking_data
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Тестовое бронирование создано")
                    
                    # Получаем календарь снова
                    response = requests.get(f"{BASE_URL}/api/bookings/calendar/", headers=headers)
                    if response.status_code == 200:
                        calendar_data = response.json()
                        if isinstance(calendar_data, dict):
                            bookings = calendar_data.get("results", [])
                        else:
                            bookings = calendar_data
    
    if len(bookings) == 0:
        print("❌ Не удалось получить бронирования для проверки")
        return
    
    # Проверяем первое бронирование
    booking = bookings[0]
    print(f"\nПроверка бронирования ID: {booking.get('id')}")
    print(f"Поля в ответе: {', '.join(booking.keys())}")
    
    has_status = 'status' in booking
    has_booking_status = 'bookingStatus' in booking
    
    print(f"\n✓ Поле 'status': {'✅ Есть' if has_status else '❌ Отсутствует'}")
    print(f"✓ Поле 'bookingStatus': {'✅ Есть' if has_booking_status else '❌ Отсутствует'}")
    
    if has_status:
        print(f"  Значение status: {booking['status']}")
    
    if has_booking_status:
        print(f"  Значение bookingStatus: {booking['bookingStatus']}")
        
        # Проверяем корректность значения
        status_value = booking.get('status', '')
        booking_status_value = booking.get('bookingStatus', '')
        
        expected_booking_status = 'active' if status_value in ['NEW', 'CONFIRMED'] else 'archived'
        
        if booking_status_value == expected_booking_status:
            print(f"  ✅ Значение корректно (ожидалось: {expected_booking_status})")
        else:
            print(f"  ❌ Значение некорректно (ожидалось: {expected_booking_status}, получено: {booking_status_value})")
    
    # 4. Итоговая проверка
    print("\n" + "="*80)
    if has_status and has_booking_status:
        print("ТЕСТ ПРОЙДЕН ✅")
        print("Календарь возвращает оба поля: status и bookingStatus")
    elif has_status and not has_booking_status:
        print("ТЕСТ НЕ ПРОЙДЕН ❌")
        print("Календарь возвращает только status, но не bookingStatus")
    else:
        print("ТЕСТ НЕ ПРОЙДЕН ❌")
        print("Календарь не возвращает необходимые поля")
    print("="*80)
    
    # Показываем пример ответа
    if bookings:
        print("\nПример ответа календаря:")
        print(json.dumps(bookings[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_calendar_status()
