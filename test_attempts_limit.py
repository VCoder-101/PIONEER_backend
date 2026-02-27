"""
Тест ограничения количества попыток (5 попыток)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service


def test_attempts_limit():
    """Тест ограничения попыток"""
    print("=" * 60)
    print("ТЕСТ ОГРАНИЧЕНИЯ КОЛИЧЕСТВА ПОПЫТОК")
    print("=" * 60)
    
    test_email = "test@example.com"
    correct_code = "4444"
    wrong_code = "0000"
    
    # Отправляем код
    print(f"\n1. Отправка кода на {test_email}...")
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Код: {result.get('dev_code', 'N/A')}")
    
    # Делаем 5 неверных попыток
    print(f"\n2. Делаем 5 неверных попыток с кодом {wrong_code}...")
    for i in range(1, 6):
        result = email_verification_service.verify_code(test_email, wrong_code, purpose='auth')
        print(f"   Попытка {i}: {result['error']}, осталось попыток: {result['attempts_left']}")
    
    # Пытаемся ввести правильный код после исчерпания попыток
    print(f"\n3. Пытаемся ввести правильный код {correct_code} после исчерпания попыток...")
    result = email_verification_service.verify_code(test_email, correct_code, purpose='auth')
    
    if not result['success']:
        print(f"   ✅ Правильно! Код не принимается: {result['error']}")
    else:
        print(f"   ❌ Ошибка! Код принят после исчерпания попыток")
    
    # Запрашиваем новый код
    print(f"\n4. Запрашиваем новый код...")
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Новый код: {result.get('dev_code', 'N/A')}")
    
    # Проверяем что счетчик сброшен
    print(f"\n5. Проверяем правильный код с новым счетчиком...")
    result = email_verification_service.verify_code(test_email, correct_code, purpose='auth')
    
    if result['success']:
        print(f"   ✅ Правильно! Код принят, осталось попыток было: {result['attempts_left']}")
    else:
        print(f"   ❌ Ошибка! Код не принят: {result['error']}")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_attempts_limit()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
