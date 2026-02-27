"""
Сервис для отправки email-кодов подтверждения.
Использует Django cache для хранения кодов (TTL: 5 минут).
"""
from django.core.mail import EmailMessage
from django.core.cache import cache
from django.conf import settings
import secrets
import os


class EmailVerificationService:
    """Сервис для работы с email-кодами подтверждения"""
    
    # Тестовый код для разработки
    TEST_CODE = "4444"
    CODE_TTL = 300  # 5 минут в секундах
    MAX_ATTEMPTS = 5  # Максимальное количество попыток
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pioneer.local')
        self.is_dev = getattr(settings, 'DEBUG', True)
    
    def generate_code(self, use_test_code=None):
        """
        Генерирует 4-значный код подтверждения.
        В режиме разработки можно использовать тестовый код 4444.
        """
        if use_test_code is None:
            use_test_code = self.is_dev
        
        if use_test_code:
            return self.TEST_CODE
        
        # Генерируем криптографически безопасный 4-значный код
        return ''.join([str(secrets.randbelow(10)) for _ in range(4)])
    
    def save_code_to_cache(self, email, code, purpose='auth'):
        """
        Сохраняет код в кэш Django.
        
        Args:
            email: Email пользователя
            code: Код подтверждения
            purpose: Цель кода ('auth' или 'recovery')
        """
        cache_key = f"email_code:{purpose}:{email}"
        attempts_key = f"email_attempts:{purpose}:{email}"
        
        # Сохраняем код и сбрасываем счетчик попыток
        cache.set(cache_key, code, self.CODE_TTL)
        cache.set(attempts_key, 0, self.CODE_TTL)
    
    def get_attempts_left(self, email, purpose='auth'):
        """
        Получает количество оставшихся попыток.
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            int: Количество оставшихся попыток
        """
        attempts_key = f"email_attempts:{purpose}:{email}"
        attempts = cache.get(attempts_key, 0)
        return self.MAX_ATTEMPTS - attempts
    
    def increment_attempts(self, email, purpose='auth'):
        """
        Увеличивает счетчик попыток.
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            int: Количество оставшихся попыток
        """
        attempts_key = f"email_attempts:{purpose}:{email}"
        attempts = cache.get(attempts_key, 0)
        attempts += 1
        cache.set(attempts_key, attempts, self.CODE_TTL)
        return self.MAX_ATTEMPTS - attempts
    
    def verify_code(self, email, code, purpose='auth'):
        """
        Проверяет код из кэша.
        
        Args:
            email: Email пользователя
            code: Код для проверки
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            dict: {'success': bool, 'attempts_left': int, 'error': str}
        """
        cache_key = f"email_code:{purpose}:{email}"
        attempts_key = f"email_attempts:{purpose}:{email}"
        
        # Проверяем количество попыток
        attempts = cache.get(attempts_key, 0)
        if attempts >= self.MAX_ATTEMPTS:
            return {
                'success': False,
                'attempts_left': 0,
                'error': 'Превышено количество попыток. Запросите новый код.'
            }
        
        cached_code = cache.get(cache_key)
        
        if not cached_code:
            return {
                'success': False,
                'attempts_left': self.MAX_ATTEMPTS - attempts,
                'error': 'Код не найден или истёк. Запросите новый код.'
            }
        
        if cached_code == code:
            # Код верный - удаляем код и счетчик попыток
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return {
                'success': True,
                'attempts_left': self.MAX_ATTEMPTS - attempts
            }
        else:
            # Код неверный - увеличиваем счетчик попыток
            attempts_left = self.increment_attempts(email, purpose)
            return {
                'success': False,
                'attempts_left': attempts_left,
                'error': f'Неверный код. Осталось попыток: {attempts_left}'
            }
    
    def send_auth_code(self, email):
        """
        Отправляет код для авторизации.
        
        Args:
            email: Email пользователя
        
        Returns:
            dict: {'success': bool, 'code': str (только в dev режиме)}
        """
        code = self.generate_code()
        self.save_code_to_cache(email, code, purpose='auth')
        
        subject = "🔐 Код для входа - Pioneer Study"
        html_message = self._build_auth_email_html(code)
        
        try:
            email_msg = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=self.from_email,
                to=[email]
            )
            email_msg.content_subtype = "html"
            email_msg.send()
            
            result = {'success': True}
            if self.is_dev:
                result['dev_code'] = code
            
            return result
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_recovery_code(self, email):
        """
        Отправляет код для восстановления доступа.
        
        Args:
            email: Email пользователя
        
        Returns:
            dict: {'success': bool, 'code': str (только в dev режиме)}
        """
        code = self.generate_code()
        self.save_code_to_cache(email, code, purpose='recovery')
        
        subject = "🔑 Код восстановления доступа - Pioneer Study"
        html_message = self._build_recovery_email_html(code)
        
        try:
            email_msg = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=self.from_email,
                to=[email]
            )
            email_msg.content_subtype = "html"
            email_msg.send()
            
            result = {'success': True}
            if self.is_dev:
                result['dev_code'] = code
            
            return result
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return {'success': False, 'error': str(e)}
    
    def _build_auth_email_html(self, code):
        """Создает HTML для письма авторизации"""
        return f"""
        <html>
        <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
        <td align="center" style="padding:20px 0;">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:10px;">
        <tr>
        <td style="background:#4A90E2;padding:30px;text-align:center;color:white;font-size:28px;font-weight:bold;">
        Pioneer Study
        </td>
        </tr>
        <tr>
        <td style="padding:40px 30px;">
        <h2 style="color:#333;font-size:24px;margin:0 0 20px 0;">Вход в систему</h2>
        <p style="color:#666;line-height:1.6;margin:0 0 20px 0;">Используйте этот код для входа в Pioneer Study:</p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f8f9fa;border-radius:8px;margin:20px 0;">
        <tr>
        <td style="padding:20px;text-align:center;">
        <p style="color:#666;margin:0 0 10px 0;font-size:14px;">Код подтверждения:</p>
        <div style="font-size:48px;font-weight:bold;color:#4A90E2;letter-spacing:12px;margin:10px 0;">{code}</div>
        </td>
        </tr>
        </table>
        <p style="color:#999;font-size:12px;margin:20px 0 0 0;text-align:center;">Код действителен 5 минут.</p>
        <p style="color:#999;font-size:12px;margin:10px 0 0 0;text-align:center;">Если вы не запрашивали этот код, проигнорируйте это письмо.</p>
        </td>
        </tr>
        <tr>
        <td style="background:#f8f9fa;padding:20px;text-align:center;color:#999;font-size:14px;">
        © 2025 Pioneer Study. Все права защищены.
        </td>
        </tr>
        </table>
        </td>
        </tr>
        </table>
        </body>
        </html>
        """
    
    def _build_recovery_email_html(self, code):
        """Создает HTML для письма восстановления доступа"""
        return f"""
        <html>
        <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
        <td align="center" style="padding:20px 0;">
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:10px;">
        <tr>
        <td style="background:#E74C3C;padding:30px;text-align:center;color:white;font-size:28px;font-weight:bold;">
        Pioneer Study
        </td>
        </tr>
        <tr>
        <td style="padding:40px 30px;">
        <h2 style="color:#333;font-size:24px;margin:0 0 20px 0;">Восстановление доступа</h2>
        <p style="color:#666;line-height:1.6;margin:0 0 20px 0;">Вы запросили восстановление доступа к аккаунту Pioneer Study.</p>
        <p style="color:#666;line-height:1.6;margin:0 0 20px 0;">Используйте этот код для восстановления:</p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f8f9fa;border-radius:8px;margin:20px 0;">
        <tr>
        <td style="padding:20px;text-align:center;">
        <p style="color:#666;margin:0 0 10px 0;font-size:14px;">Код восстановления:</p>
        <div style="font-size:48px;font-weight:bold;color:#E74C3C;letter-spacing:12px;margin:10px 0;">{code}</div>
        </td>
        </tr>
        </table>
        <p style="color:#999;font-size:12px;margin:20px 0 0 0;text-align:center;">Код действителен 5 минут.</p>
        <p style="color:#E74C3C;font-size:12px;margin:10px 0 0 0;text-align:center;font-weight:bold;">Если вы не запрашивали восстановление доступа, немедленно свяжитесь с поддержкой!</p>
        </td>
        </tr>
        <tr>
        <td style="background:#f8f9fa;padding:20px;text-align:center;color:#999;font-size:14px;">
        © 2025 Pioneer Study. Все права защищены.
        </td>
        </tr>
        </table>
        </td>
        </tr>
        </table>
        </body>
        </html>
        """


# Создаем глобальный экземпляр сервиса
email_verification_service = EmailVerificationService()
