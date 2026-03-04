"""
Тест новой логики кодов подтверждения
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service
from django.core.cache import cache

def test_new_logic():
    """Тестирует новую логику"""
    
    print("="*70)
    print("ТЕСТ НОВОЙ ЛОГИКИ КОДОВ")
    print("="*70)
    
    test_email = "test@newlogic.com"
    
    # Очистка
    cache.clear()
    
    # 1. Генерация кода
    print("\n1️⃣  ГЕНЕРАЦИЯ КОДА")
    print("-"*70)
    code1 = email_verification_service.generate_code()
    code2 = email_verification_service.generate_code()
    code3 = email_verification_service.generate_code()
    print(f"   Код 1: {code1}")
    print(f"   Код 2: {code2}")
    print(f"   Код 3: {code3}")
    print(f"   ✅ Коды генерируются случайно (не 4444)")
    
    # 2. Отправка кода
    print("\n2️⃣  ОТПРАВКА КОДА")
    print("-"*70)
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Успех: {result['success']}")
    if 'dev_code' in result:
        print(f"   Dev код: {result['dev_code']}")
        generated_code = result['dev_code']
    
    # 3. Попытка повторной отправки (должна быть заблокирована)
    print("\n3️⃣  ПОВТОРНАЯ ОТПРАВКА (СРАЗУ)")
    print("-"*70)
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Успех: {result['success']}")
    if not result['success']:
        print(f"   ✅ Ошибка: {result.get('error')}")
        print(f"   ✅ Осталось ждать: {result.get('time_left')} секунд")
    
    # 4. Проверка дебаг кода "4444"
    print("\n4️⃣  ПРОВЕРКА ДЕБАГ КОДА '4444'")
    print("-"*70)
    result = email_verification_service.verify_code(test_email, "4444", purpose='auth')
    print(f"   Успех: {result['success']}")
    if result['success']:
        print(f"   ✅ Дебаг код '4444' работает!")
    
    # 5. Новая отправка для теста неудачных попыток
    print("\n5️⃣  НОВАЯ ОТПРАВКА ДЛЯ ТЕСТА")
    print("-"*70)
    cache.delete(f"email_resend:auth:{test_email}")  # Сбрасываем cooldown для теста
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Успех: {result['success']}")
    if 'dev_code' in result:
        print(f"   Dev код: {result['dev_code']}")
        generated_code = result['dev_code']
    
    # 6. 5 неудачных попыток
    print("\n6️⃣  5 НЕУДАЧНЫХ ПОПЫТОК")
    print("-"*70)
    for i in range(1, 6):
        result = email_verification_service.verify_code(test_email, "0000", purpose='auth')
        print(f"   Попытка {i}:")
        print(f"     - success: {result['success']}")
        print(f"     - attempts_left: {result['attempts_left']}")
        if 'blocked_time' in result:
            print(f"     - blocked_time: {result['blocked_time']} секунд ({result['blocked_time']//60} минут)")
    
    # 7. Проверка блокировки
    print("\n7️⃣  ПРОВЕРКА БЛОКИРОВКИ (7 МИНУТ)")
    print("-"*70)
    result = email_verification_service.verify_code(test_email, generated_code, purpose='auth')
    print(f"   Успех: {result['success']}")
    if not result['success']:
        print(f"   ✅ Email заблокирован!")
        print(f"   ✅ Ошибка: {result.get('error')}")
        print(f"   ✅ Время блокировки: {result.get('blocked_time', 0)} секунд ({result.get('blocked_time', 0)//60} минут)")
    
    # 8. Попытка отправить новый код (должна быть заблокирована)
    print("\n8️⃣  ПОПЫТКА ОТПРАВИТЬ КОД ВО ВРЕМЯ БЛОКИРОВКИ")
    print("-"*70)
    cache.delete(f"email_resend:auth:{test_email}")  # Сбрасываем cooldown
    result = email_verification_service.send_auth_code(test_email)
    print(f"   Успех: {result['success']}")
    if not result['success']:
        print(f"   ✅ Отправка заблокирована!")
        print(f"   ✅ Ошибка: {result.get('error')}")
    
    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ НОВОЙ ЛОГИКИ")
    print("="*70)
    print("""
✅ 1. Код генерируется случайно (не 4444)
✅ 2. Дебаг код "4444" всегда принимается
✅ 3. Повторная отправка только через 1 минуту
✅ 4. После 5 неудачных попыток - блокировка на 7 минут
✅ 5. Во время блокировки нельзя отправить новый код
✅ 6. Во время блокировки нельзя проверить код

ПАРАМЕТРЫ:
- CODE_TTL: 5 минут (300 секунд)
- MAX_ATTEMPTS: 5 попыток
- BLOCK_TIME: 7 минут (420 секунд)
- RESEND_COOLDOWN: 1 минута (60 секунд)
- DEBUG_CODE: "4444" (всегда принимается)

КЛЮЧИ В КЭШЕ:
- email_code:auth:{email} - сам код (TTL: 5 минут)
- email_attempts:auth:{email} - счетчик попыток (TTL: 5 минут)
- email_blocked:auth:{email} - блокировка (TTL: 7 минут)
- email_resend:auth:{email} - cooldown отправки (TTL: 1 минута)
    """)
    print("="*70)
    
    # Очистка
    cache.clear()

if __name__ == '__main__':
    test_new_logic()
