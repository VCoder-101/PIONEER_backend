"""
Тест для БАГ-001: Проверка инвалидации старого access токена после обновления через refresh token.

Шаги воспроизведения:
1. Выполнить авторизацию, получить access token
2. Выполнить запрос /api/users/auth/jwt/verify/ с текущим токеном
3. Сменить access token с помощью refresh token
4. Сразу после смены выполнить запрос: /api/users/auth/jwt/verify/ со старым access token

Ожидаемый результат: Токен должен быть аннулирован, API возвращает ошибку «Token is expired»
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_token_invalidation():
    print("=" * 80)
    print("ТЕСТ БАГ-001: Инвалидация старого access токена")
    print("=" * 80)
    
    # Шаг 1: Авторизация
    print("\n1. Авторизация пользователя...")
    email = "test_bug001@example.com"
    device_id = "test-device-bug001"
    
    # Отправляем код
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
    
    # Получаем dev_code из ответа
    dev_code = send_response.json().get("dev_code")
    if not dev_code:
        print("   ❌ dev_code не найден в ответе")
        return
    
    print(f"   Dev код: {dev_code}")
    
    # Верифицируем код
    verify_response = requests.post(
        f"{BASE_URL}/api/users/auth/verify-code/",
        json={
            "email": email,
            "code": dev_code,
            "device_id": device_id,
            "name": "Test User Bug 001",
            "privacy_policy_accepted": True
        }
    )
    print(f"   Верификация кода: {verify_response.status_code}")
    
    if verify_response.status_code != 200:
        print(f"   ❌ Ошибка верификации: {verify_response.text}")
        return
    
    auth_data = verify_response.json()
    old_access_token = auth_data["jwt"]["access"]
    refresh_token = auth_data["jwt"]["refresh"]
    
    print(f"   ✅ Получен access token: {old_access_token[:50]}...")
    print(f"   ✅ Получен refresh token: {refresh_token[:50]}...")
    
    # Шаг 2: Проверяем старый токен (должен работать)
    print("\n2. Проверка старого access токена (должен быть валидным)...")
    verify_old_response = requests.post(
        f"{BASE_URL}/api/users/auth/jwt/verify/",
        json={"token": old_access_token}
    )
    print(f"   Статус: {verify_old_response.status_code}")
    
    if verify_old_response.status_code == 200:
        print(f"   ✅ Старый токен валиден (ожидаемо)")
        print(f"   Пользователь: {verify_old_response.json()['user']['email']}")
    else:
        print(f"   ❌ Старый токен невалиден (неожиданно): {verify_old_response.text}")
        return
    
    # Шаг 3: Обновляем токен через refresh
    print("\n3. Обновление токена через refresh token...")
    refresh_response = requests.post(
        f"{BASE_URL}/api/token/refresh/",
        json={
            "refresh": refresh_token,
            "device_id": device_id
        }
    )
    print(f"   Статус: {refresh_response.status_code}")
    
    if refresh_response.status_code != 200:
        print(f"   ❌ Ошибка обновления токена: {refresh_response.text}")
        return
    
    refresh_data = refresh_response.json()
    new_access_token = refresh_data["access"]
    
    print(f"   ✅ Получен новый access token: {new_access_token[:50]}...")
    
    # Шаг 4: Проверяем старый токен (должен быть инвалидирован)
    print("\n4. Проверка СТАРОГО access токена после обновления (должен быть инвалидирован)...")
    verify_old_after_refresh = requests.post(
        f"{BASE_URL}/api/users/auth/jwt/verify/",
        json={"token": old_access_token}
    )
    print(f"   Статус: {verify_old_after_refresh.status_code}")
    
    if verify_old_after_refresh.status_code == 401:
        error_msg = verify_old_after_refresh.json().get("error", "")
        if "expired" in error_msg.lower():
            print(f"   ✅ ТЕСТ ПРОЙДЕН! Старый токен инвалидирован: {error_msg}")
        else:
            print(f"   ⚠️  Токен инвалидирован, но сообщение не содержит 'expired': {error_msg}")
    else:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Старый токен все еще валиден!")
        print(f"   Ответ: {verify_old_after_refresh.text}")
        return
    
    # Шаг 5: Проверяем новый токен (должен работать)
    print("\n5. Проверка НОВОГО access токена (должен быть валидным)...")
    verify_new_response = requests.post(
        f"{BASE_URL}/api/users/auth/jwt/verify/",
        json={"token": new_access_token}
    )
    print(f"   Статус: {verify_new_response.status_code}")
    
    if verify_new_response.status_code == 200:
        print(f"   ✅ Новый токен валиден (ожидаемо)")
        print(f"   Пользователь: {verify_new_response.json()['user']['email']}")
    else:
        print(f"   ❌ Новый токен невалиден (неожиданно): {verify_new_response.text}")
        return
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-001 ИСПРАВЛЕН!")
    print("=" * 80)


if __name__ == "__main__":
    test_token_invalidation()
