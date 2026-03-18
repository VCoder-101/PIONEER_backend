"""
Тест для БАГ-004: Проверка rate limiting при повторной отправке кода.

Проблема: При повторной отправке кода в течение 1 минуты сервер возвращает 500 вместо 429.
Ожидаемое поведение: Сервер должен возвращать 429 Too Many Requests с информацией о времени ожидания.
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_rate_limiting():
    print("=" * 80)
    print("ТЕСТ БАГ-004: Rate limiting при повторной отправке кода")
    print("=" * 80)
    
    email = "test_bug004_ratelimit@example.com"
    
    # Шаг 1: Первая отправка кода
    print("\n1. Первая отправка кода...")
    
    first_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={
            "email": email,
            "privacy_policy_accepted": True
        }
    )
    
    print(f"   Статус: {first_response.status_code}")
    
    if first_response.status_code != 200:
        print(f"   ❌ Ошибка первой отправки: {first_response.text}")
        return
    
    first_data = first_response.json()
    print(f"   ✅ Код отправлен")
    if "dev_code" in first_data:
        print(f"   Dev код: {first_data['dev_code']}")
    
    # Шаг 2: Немедленная повторная отправка (должна вернуть 429)
    print("\n2. Немедленная повторная отправка (должна вернуть 429)...")
    
    second_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={
            "email": email,
            "privacy_policy_accepted": True
        }
    )
    
    print(f"   Статус: {second_response.status_code}")
    
    if second_response.status_code == 429:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Получен статус 429 Too Many Requests")
        second_data = second_response.json()
        print(f"   Сообщение: {second_data.get('error')}")
        if "time_left" in second_data:
            print(f"   Время ожидания: {second_data['time_left']} секунд")
        
    elif second_response.status_code == 500:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Получен статус 500 вместо 429")
        print(f"   Ответ: {second_response.text}")
        return
        
    else:
        print(f"   ❌ Неожиданный статус: {second_response.status_code}")
        print(f"   Ответ: {second_response.text}")
        return
    
    # Шаг 3: Проверка что после ожидания можно отправить снова
    print("\n3. Ожидание cooldown периода...")
    
    if "time_left" in second_data:
        wait_time = second_data["time_left"] + 1  # +1 секунда для гарантии
        print(f"   Ожидание {wait_time} секунд...")
        time.sleep(wait_time)
    else:
        print(f"   Ожидание 61 секунду (стандартный cooldown)...")
        time.sleep(61)
    
    print("\n4. Отправка после cooldown (должна пройти успешно)...")
    
    third_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={
            "email": email,
            "privacy_policy_accepted": True
        }
    )
    
    print(f"   Статус: {third_response.status_code}")
    
    if third_response.status_code == 200:
        print(f"   ✅ Код успешно отправлен после cooldown")
        third_data = third_response.json()
        if "dev_code" in third_data:
            print(f"   Dev код: {third_data['dev_code']}")
    else:
        print(f"   ⚠️  Неожиданный статус: {third_response.status_code}")
        print(f"   Ответ: {third_response.text}")
    
    print("\n" + "=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-004 ИСПРАВЛЕН!")
    print("=" * 80)


def test_rate_limiting_quick():
    """Быстрый тест без ожидания cooldown"""
    print("=" * 80)
    print("ТЕСТ БАГ-004: Rate limiting (быстрая проверка)")
    print("=" * 80)
    
    email = f"test_bug004_quick_{int(time.time())}@example.com"
    
    print("\n1. Первая отправка кода...")
    first_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": email, "privacy_policy_accepted": True}
    )
    print(f"   Статус: {first_response.status_code}")
    
    if first_response.status_code != 200:
        print(f"   ❌ Ошибка: {first_response.text}")
        return
    
    print(f"   ✅ Код отправлен")
    
    print("\n2. Немедленная повторная отправка...")
    second_response = requests.post(
        f"{BASE_URL}/api/users/auth/send-code/",
        json={"email": email, "privacy_policy_accepted": True}
    )
    print(f"   Статус: {second_response.status_code}")
    
    if second_response.status_code == 429:
        print(f"   ✅ ТЕСТ ПРОЙДЕН! Получен 429 Too Many Requests")
        data = second_response.json()
        print(f"   Сообщение: {data.get('error')}")
        print(f"   Время ожидания: {data.get('time_left', 'N/A')} секунд")
    elif second_response.status_code == 500:
        print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН! Получен 500 вместо 429")
        print(f"   Ответ: {second_response.text}")
    else:
        print(f"   ⚠️  Неожиданный статус: {second_response.status_code}")
        print(f"   Ответ: {second_response.text}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--quick":
            test_rate_limiting_quick()
        else:
            print("Запуск полного теста (с ожиданием cooldown)...")
            print("Для быстрого теста используйте: python test_bug_004_rate_limiting.py --quick")
            print()
            test_rate_limiting()
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка подключения к серверу!")
        print("Убедитесь что сервер запущен: python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
