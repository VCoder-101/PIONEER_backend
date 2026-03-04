"""
Тест системы ограничения попыток
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service
from django.core.cache import cache

def test_attempts_system():
    """Тестирует систему ограничения попыток"""
    
    print("="*70)
    print("ТЕСТ СИСТЕМЫ ОГРАНИЧЕНИЯ ПОПЫТОК")
    print("="*70)
    
    test_email = "test@attempts.com"
    
    # Очистка перед тестом
    cache.delete(f"email_code:auth:{test_email}")
    cache.delete(f"email_attempts:auth:{test_email}")
    
    # 1. Отправка кода
    print("\n1️⃣  ОТПРАВКА КОДА")
    print("-"*70)
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Код отправлен: {result['success']}")
    print(f"   Dev код: {result.get('dev_code', 'N/A')}")
    correct_code = result.get('dev_code', '4444')
    
    # 2. Проверка ограничения попыток
    print("\n2️⃣  ПРОВЕРКА ОГРАНИЧЕНИЯ ПОПЫТОК")
    print("-"*70)
    print(f"   Максимум попыток: {email_verification_service.MAX_ATTEMPTS}")
    print(f"   TTL кода: {email_verification_service.CODE_TTL} секунд ({email_verification_service.CODE_TTL/60} минут)")
    
    # 3. Неверные попытки
    print("\n3️⃣  НЕВЕРНЫЕ ПОПЫТКИ")
    print("-"*70)
    
    for i in range(1, 6):
        result = email_verification_service.verify_code(test_email, "0000", purpose='auth')
        print(f"   Попытка {i}:")
        print(f"     - success: {result['success']}")
        print(f"     - attempts_left: {result['attempts_left']}")
        print(f"     - error: {result.get('error', 'N/A')}")
    
    # 4. Попытка после превышения лимита
    print("\n4️⃣  ПОПЫТКА ПОСЛЕ ПРЕВЫШЕНИЯ ЛИМИТА")
    print("-"*70)
    result = email_verification_service.verify_code(test_email, "0000", purpose='auth')
    print(f"   success: {result['success']}")
    print(f"   attempts_left: {result['attempts_left']}")
    print(f"   error: {result.get('error', 'N/A')}")
    
    # 5. Попытка с правильным кодом после превышения лимита
    print("\n5️⃣  ПРАВИЛЬНЫЙ КОД ПОСЛЕ ПРЕВЫШЕНИЯ ЛИМИТА")
    print("-"*70)
    result = email_verification_service.verify_code(test_email, correct_code, purpose='auth')
    print(f"   success: {result['success']}")
    print(f"   error: {result.get('error', 'N/A')}")
    if not result['success']:
        print(f"   ❌ Даже правильный код не работает после 5 попыток!")
    
    # 6. Запрос нового кода (сброс счетчика)
    print("\n6️⃣  ЗАПРОС НОВОГО КОДА (СБРОС СЧЕТЧИКА)")
    print("-"*70)
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Новый код отправлен: {result['success']}")
    print(f"   Dev код: {result.get('dev_code', 'N/A')}")
    new_code = result.get('dev_code', '4444')
    
    # 7. Проверка что счетчик сброшен
    print("\n7️⃣  ПРОВЕРКА СБРОСА СЧЕТЧИКА")
    print("-"*70)
    attempts_left = email_verification_service.get_attempts_left(test_email, purpose='auth')
    print(f"   Осталось попыток: {attempts_left}")
    
    # 8. Проверка нового кода
    print("\n8️⃣  ПРОВЕРКА НОВОГО КОДА")
    print("-"*70)
    result = email_verification_service.verify_code(test_email, new_code, purpose='auth')
    print(f"   success: {result['success']}")
    if result['success']:
        print(f"   ✅ Новый код работает!")
    
    # 9. Проверка что код и счетчик удалены после успешной проверки
    print("\n9️⃣  ПРОВЕРКА УДАЛЕНИЯ КОДА И СЧЕТЧИКА")
    print("-"*70)
    code_key = f"email_code:auth:{test_email}"
    attempts_key = f"email_attempts:auth:{test_email}"
    code_exists = cache.get(code_key) is not None
    attempts_exists = cache.get(attempts_key) is not None
    print(f"   Код в кэше: {code_exists}")
    print(f"   Счетчик в кэше: {attempts_exists}")
    if not code_exists and not attempts_exists:
        print(f"   ✅ Код и счетчик удалены после успешной проверки")
    
    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ")
    print("="*70)
    print("""
КАК РАБОТАЕТ СИСТЕМА:

1. ОГРАНИЧЕНИЕ ПОПЫТОК:
   - Максимум 5 попыток ввода кода
   - После 5 неудачных попыток код блокируется
   - Даже правильный код не работает после блокировки

2. СБРОС СЧЕТЧИКА:
   - Запрос нового кода СБРАСЫВАЕТ счетчик попыток
   - Новый код = новые 5 попыток
   - Старый код становится недействительным

3. TTL (ВРЕМЯ ЖИЗНИ):
   - Код живет 5 минут
   - Счетчик попыток живет 5 минут
   - После истечения времени код автоматически удаляется

4. УСПЕШНАЯ ПРОВЕРКА:
   - При правильном коде: код и счетчик удаляются из кэша
   - Повторное использование кода невозможно
   - Коды одноразовые

5. КАК СНЯТЬ БЛОКИРОВКУ:
   ✅ Запросить новый код (POST /api/users/auth/send-code/)
   ✅ Подождать 5 минут (код истечет автоматически)
   ❌ Нельзя просто продолжить попытки

БЕЗОПАСНОСТЬ:
✅ Защита от брутфорса (5 попыток)
✅ Коды одноразовые
✅ Коды короткоживущие (5 минут)
✅ Автоматическая очистка кэша
    """)
    print("="*70)
    
    # Очистка после теста
    cache.delete(f"email_code:auth:{test_email}")
    cache.delete(f"email_attempts:auth:{test_email}")

if __name__ == '__main__':
    test_attempts_system()
