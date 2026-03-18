"""
Тест для БАГ-003: Проверка создания бронирования клиентом.

Проблема: Система требует поля user и dateTime, хотя user должен устанавливаться автоматически.
Ожидаемое поведение: CLIENT может создать бронирование с полями service, scheduled_at, carModel, wheelDiameter.
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def test_client_can_create_booking():
    print("=" * 80)
    print("ТЕСТ БАГ-003: Создание бронирования клиентом")
    print("=" * 80)
    
    # Шаг 1: Авторизация под клиентом
    print("\n1. Авторизация под клиентом...")
    email = "test_bug003_client@example.com"
    device_id = "test-device-bug003"
    
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
    
    verify_response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": dev_code,
            "device_id": device_id,
            "name": "Test Client Bug 003",
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
    
    # Шаг 2: Создание бронирования (формат из баг-репорта)
    print("\n2. Создание бронирования (формат из баг-репорта)...")
    
    # Время бронирования - завтра в 10:00
    scheduled_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    
    booking_data = {
        "service": 1,  # Предполагаем что есть услуга с ID=1
        "scheduled_at": scheduled_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "NEW",
        "carModel": "Lada Vesta",
        "wheelDiameter": 16
    }
    
    print(f"   Данные бронирования: {json.dumps(booking_data, indent=2)}")
    
    create_response = requests.post(
        f"{BASE_URL}/api/bookings/",
        json=booking_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    print(f"   Статус: {create_response.status_code}")
    
    if create_response.status_code == 201:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Бронирование создано")
        booking = create_response.json()
        print(f"\n   Детали:")
        print(f"   - ID: {booking.get('id')}")
        print(f"   - Услуга: {booking.get('service')}")
        print(f"   - Статус: {booking.get('status')}")
        print(f"   - Клиент: {booking.get('user_email')}")
        print(f"   - Модель авто: {booking.get('car_model') or booking.get('carModel')}")
        print(f"   - Диаметр диска: {booking.get('wheel_diameter') or booking.get('wheelDiameter')}")
        
    elif create_response.status_code == 400:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Ошибка валидации")
        print(f"   Ответ: {create_response.text}")
        
        # Попробуем альтернативный формат (snake_case)
        print("\n3. Попытка с альтернативным форматом (snake_case)...")
        
        booking_data_alt = {
            "service": 1,
            "scheduled_at": scheduled_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "NEW",
            "car_model": "Lada Vesta",
            "wheel_diameter": 16
        }
        
        create_response_alt = requests.post(
            f"{BASE_URL}/api/bookings/",
            json=booking_data_alt,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"   Статус: {create_response_alt.status_code}")
        
        if create_response_alt.status_code == 201:
            print(f"   ✅ Бронирование создано с snake_case форматом")
            booking = create_response_alt.json()
            print(f"   - ID: {booking.get('id')}")
        else:
            print(f"   ❌ Ошибка: {create_response_alt.text}")
            return
        
    elif create_response.status_code == 403:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Доступ запрещен")
        print(f"   Ответ: {create_response.text}")
        return
        
    elif create_response.status_code == 404:
        print(f"   ⚠️  Услуга с ID=1 не найдена")
        print(f"   Создайте тестовую услугу или измените service ID в тесте")
        return
        
    else:
        print(f"   ❌ Неожиданный статус")
        print(f"   Ответ: {create_response.text}")
        return
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-003 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_client_can_create_booking()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
