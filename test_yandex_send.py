"""
Тест отправки письма через Яндекс SMTP на akk2_mghmhj@mail.ru
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from users.email_service import email_verification_service

print("=" * 70)
print("ТЕСТ ОТПРАВКИ ЧЕРЕЗ ЯНДЕКС SMTP")
print("=" * 70)

print(f"\nНастройки:")
print(f"  Сервер: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"  SSL: {settings.EMAIL_USE_SSL}")
print(f"  От кого: {settings.EMAIL_HOST_USER}")
print(f"  Получатель: akk2_mghmhj@mail.ru")

# Тест 1: Простое текстовое письмо
print("\n" + "-" * 70)
print("ТЕСТ 1: Простое текстовое письмо")
print("-" * 70)

try:
    result = send_mail(
        subject='Тест отправки - Pioneer Study',
        message='Привет! Это тестовое письмо для проверки SMTP.\n\nЕсли вы видите это письмо, значит отправка работает!',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=['akk2_mghmhj@mail.ru'],
        fail_silently=False,
    )
    print(f"✅ Простое письмо отправлено (result={result})")
except Exception as e:
    print(f"❌ Ошибка отправки простого письма:")
    print(f"   {type(e).__name__}: {e}")

# Тест 2: HTML письмо
print("\n" + "-" * 70)
print("ТЕСТ 2: HTML письмо")
print("-" * 70)

from django.core.mail import EmailMessage

html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
        <h2 style="color: #4A90E2;">Тест HTML письма</h2>
        <p>Это тестовое HTML письмо от <strong>Pioneer Study</strong>.</p>
        <div style="background: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; font-size: 18px; color: #4A90E2;">
                ✅ Если вы видите это письмо, значит SMTP работает отлично!
            </p>
        </div>
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            © 2025 Pioneer Study. Все права защищены.
        </p>
    </div>
</body>
</html>
"""

try:
    email = EmailMessage(
        subject='Тест HTML - Pioneer Study',
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=['akk2_mghmhj@mail.ru']
    )
    email.content_subtype = "html"
    email.send()
    print("✅ HTML письмо отправлено")
except Exception as e:
    print(f"❌ Ошибка отправки HTML письма:")
    print(f"   {type(e).__name__}: {e}")

# Тест 3: Код подтверждения (полный шаблон)
print("\n" + "-" * 70)
print("ТЕСТ 3: Код подтверждения (полный шаблон Pioneer Study)")
print("-" * 70)

result = email_verification_service.send_auth_code('akk2_mghmhj@mail.ru')

if result['success']:
    print("✅ Код подтверждения отправлен")
    if 'dev_code' in result:
        print(f"   Код: {result['dev_code']}")
else:
    print(f"❌ Ошибка отправки кода:")
    print(f"   {result.get('error', 'Неизвестная ошибка')}")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 70)
print("\n📧 Проверьте почту akk2_mghmhj@mail.ru")
print("   Должно прийти 3 письма:")
print("   1. Простое текстовое письмо")
print("   2. HTML письмо")
print("   3. Код подтверждения с красивым шаблоном")
print("=" * 70)
