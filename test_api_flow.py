"""
Тест полного цикла авторизации через API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from django.test import RequestFactory
from users.email_auth_views import send_email_auth_code, verify_email_auth_code
import json


def test_full_auth_flow():
    """Тест полного цикла авторизации"""
    factory = RequestFactory()
    
    print("=" * 60)
    print("ТЕСТ ПОЛНОГО ЦИКЛА АВТОРИЗАЦИИ")
    print("=" * 60)
    
    # Шаг 1: Отправка кода
    print("\n1. Отправка кода на test@example.com...")
    request = factory.post(
        '/api/users/auth/email/send-code/',
        data=json.dumps({
            'email': 'test@example.com',
            'privacy_policy_accepted': True
        }),
        content_type='application/json'
    )
    
    response = send_email_auth_code(request)
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.data}")
    
    if response.status_code != 200:
        print("❌ Ошибка при отправке кода")
        return
    
    print("✅ Код отправлен")
    
    # Шаг 2: Проверка кода
    print("\n2. Проверка кода 4444...")
    request = factory.post(
        '/api/users/auth/email/verify-code/',
        data=json.dumps({
            'email': 'test@example.com',
            'code': '4444',
            'device_id': 'test-device-123',
            'privacy_policy_accepted': True
        }),
        content_type='application/json'
    )
    
    response = verify_email_auth_code(request)
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Авторизация успешна!")
        print(f"   User ID: {response.data['user']['id']}")
        print(f"   Email: {response.data['user']['email']}")
        print(f"   Role: {response.data['user']['role']}")
        print(f"   Is New: {response.data['user']['is_new']}")
        print(f"   JWT Access: {response.data['jwt']['access'][:50]}...")
    else:
        print(f"❌ Ошибка: {response.data}")
    
    # Шаг 3: Попытка повторного использования кода
    print("\n3. Попытка повторного использования кода...")
    request = factory.post(
        '/api/users/auth/email/verify-code/',
        data=json.dumps({
            'email': 'test@example.com',
            'code': '4444',
            'device_id': 'test-device-456',
            'privacy_policy_accepted': True
        }),
        content_type='application/json'
    )
    
    response = verify_email_auth_code(request)
    
    if response.status_code != 200:
        print("✅ Код нельзя использовать повторно (правильно!)")
        print(f"   Ошибка: {response.data.get('error')}")
    else:
        print("❌ Код можно использовать повторно (ошибка!)")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_full_auth_flow()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
