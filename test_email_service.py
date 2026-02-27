"""
Тестовый скрипт для проверки отправки email-кодов.
Запуск: python test_email_service.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service


def test_auth_code():
    """Тест отправки кода авторизации"""
    print("=" * 60)
    print("Тест отправки кода авторизации")
    print("=" * 60)
    
    test_email = input("Введите email для теста (или Enter для test@example.com): ").strip()
    if not test_email:
        test_email = "test@example.com"
    
    print(f"\nОтправка кода на {test_email}...")
    result = email_verification_service.send_auth_code(test_email)
    
    if result['success']:
        print("✅ Код успешно отправлен!")
        if 'dev_code' in result:
            print(f"🔑 Тестовый код: {result['dev_code']}")
    else:
        print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
    
    return result


def test_recovery_code():
    """Тест отправки кода восстановления"""
    print("\n" + "=" * 60)
    print("Тест отправки кода восстановления")
    print("=" * 60)
    
    test_email = input("Введите email для теста (или Enter для test@example.com): ").strip()
    if not test_email:
        test_email = "test@example.com"
    
    print(f"\nОтправка кода восстановления на {test_email}...")
    result = email_verification_service.send_recovery_code(test_email)
    
    if result['success']:
        print("✅ Код восстановления успешно отправлен!")
        if 'dev_code' in result:
            print(f"🔑 Тестовый код: {result['dev_code']}")
    else:
        print(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
    
    return result


def test_code_verification():
    """Тест проверки кода"""
    print("\n" + "=" * 60)
    print("Тест проверки кода")
    print("=" * 60)
    
    test_email = "test@example.com"
    test_code = "4444"
    
    # Сначала отправим код
    print(f"\n1. Отправка кода на {test_email}...")
    result = email_verification_service.send_auth_code(test_email)
    
    if not result['success']:
        print(f"❌ Не удалось отправить код: {result.get('error')}")
        return
    
    print("✅ Код отправлен")
    
    # Проверим код
    print(f"\n2. Проверка кода {test_code}...")
    is_valid = email_verification_service.verify_code(test_email, test_code, purpose='auth')
    
    if is_valid:
        print("✅ Код верный!")
    else:
        print("❌ Код неверный или истёк")
    
    # Попробуем проверить еще раз (должно не сработать, т.к. код удаляется)
    print(f"\n3. Повторная проверка того же кода...")
    is_valid_again = email_verification_service.verify_code(test_email, test_code, purpose='auth')
    
    if not is_valid_again:
        print("✅ Код нельзя использовать повторно (правильно!)")
    else:
        print("❌ Код можно использовать повторно (ошибка!)")


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ EMAIL СЕРВИСА")
    print("=" * 60)
    
    while True:
        print("\nВыберите тест:")
        print("1. Отправка кода авторизации")
        print("2. Отправка кода восстановления")
        print("3. Проверка работы кодов (полный цикл)")
        print("4. Выход")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == '1':
            test_auth_code()
        elif choice == '2':
            test_recovery_code()
        elif choice == '3':
            test_code_verification()
        elif choice == '4':
            print("\nДо свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем. До свидания!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
