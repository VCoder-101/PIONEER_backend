import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service

print('=' * 60)
print('Тест отправки письма (console backend)')
print('Письмо будет выведено в консоль ниже')
print('=' * 60)

result = email_verification_service.send_auth_code('test@example.com')

if result['success']:
    print('\n✅ Письмо успешно "отправлено" (выведено в консоль выше)')
    if 'dev_code' in result:
        print(f'🔑 Тестовый код: {result["dev_code"]}')
else:
    print(f'\n❌ Ошибка: {result.get("error", "Неизвестная ошибка")}')
