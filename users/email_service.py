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
    
    # Тестовый код для дебага (всегда принимается)
    DEBUG_CODE = "4444"
    CODE_TTL = 300  # 5 минут в секундах
    MAX_ATTEMPTS = 5  # Максимальное количество попыток
    BLOCK_TIME = 420  # 7 минут блокировки после 5 неудачных попыток
    RESEND_COOLDOWN = 60  # 1 минута между отправками кода
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Dmitry4424@yandex.ru')
        self.is_dev = getattr(settings, 'DEBUG', True)
    
    def generate_code(self):
        """
        Генерирует уникальный 4-значный код подтверждения.
        Код НЕ должен повторяться.
        """
        # Генерируем криптографически безопасный 4-значный код
        return ''.join([str(secrets.randbelow(10)) for _ in range(4)])
    
    def is_email_blocked(self, email, purpose='auth'):
        """
        Проверяет заблокирован ли email после превышения попыток.
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            dict: {'blocked': bool, 'time_left': int (секунды)}
        """
        block_key = f"email_blocked:{purpose}:{email}"
        block_time = cache.get(block_key)
        
        if block_time:
            return {
                'blocked': True,
                'time_left': block_time
            }
        
        return {'blocked': False, 'time_left': 0}
    
    def block_email(self, email, purpose='auth'):
        """
        Блокирует email на BLOCK_TIME секунд.
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        """
        block_key = f"email_blocked:{purpose}:{email}"
        cache.set(block_key, self.BLOCK_TIME, self.BLOCK_TIME)
    
    def can_resend_code(self, email, purpose='auth'):
        """
        Проверяет можно ли отправить код повторно (прошла ли минута).
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            dict: {'can_resend': bool, 'time_left': int (секунды)}
        """
        resend_key = f"email_resend:{purpose}:{email}"
        time_left = cache.get(resend_key)
        
        if time_left:
            return {
                'can_resend': False,
                'time_left': time_left
            }
        
        return {'can_resend': True, 'time_left': 0}
    
    def set_resend_cooldown(self, email, purpose='auth'):
        """
        Устанавливает cooldown на повторную отправку кода (1 минута).
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        """
        resend_key = f"email_resend:{purpose}:{email}"
        cache.set(resend_key, self.RESEND_COOLDOWN, self.RESEND_COOLDOWN)
    
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
        
        ВАЖНО: TTL счетчика обновляется при каждой попытке на 5 минут.
        Это значит 5 попыток считаются в течение 5 минут с момента ПОСЛЕДНЕЙ попытки.
        
        Пример:
        10:00 - Попытка 1 → счетчик истечет в 10:05
        10:01 - Попытка 2 → счетчик истечет в 10:06
        10:02 - Попытка 3 → счетчик истечет в 10:07
        10:03 - Попытка 4 → счетчик истечет в 10:08
        10:04 - Попытка 5 → блокировка на 7 минут (до 10:11)
        
        Args:
            email: Email пользователя
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            int: Количество оставшихся попыток
        """
        attempts_key = f"email_attempts:{purpose}:{email}"
        attempts = cache.get(attempts_key, 0)
        attempts += 1
        
        # Сохраняем с TTL 5 минут (обновляется при каждой попытке)
        cache.set(attempts_key, attempts, self.CODE_TTL)
        
        # Если исчерпаны все попытки - блокируем email на 7 минут
        if attempts >= self.MAX_ATTEMPTS:
            self.block_email(email, purpose)
        
        return self.MAX_ATTEMPTS - attempts
    
    def verify_code(self, email, code, purpose='auth'):
        """
        Проверяет код из кэша.
        Код принимается если он равен сгенерированному ИЛИ равен "4444" (для дебага).
        
        Args:
            email: Email пользователя
            code: Код для проверки
            purpose: Цель кода ('auth' или 'recovery')
        
        Returns:
            dict: {'success': bool, 'attempts_left': int, 'error': str, 'blocked_time': int}
        """
        cache_key = f"email_code:{purpose}:{email}"
        attempts_key = f"email_attempts:{purpose}:{email}"
        
        # Проверяем блокировку email
        block_status = self.is_email_blocked(email, purpose)
        if block_status['blocked']:
            return {
                'success': False,
                'attempts_left': 0,
                'blocked_time': block_status['time_left'],
                'error': f'Email заблокирован на {block_status["time_left"] // 60} минут после превышения попыток.'
            }
        
        # Проверяем количество попыток
        attempts = cache.get(attempts_key, 0)
        if attempts >= self.MAX_ATTEMPTS:
            # Блокируем email
            self.block_email(email, purpose)
            return {
                'success': False,
                'attempts_left': 0,
                'blocked_time': self.BLOCK_TIME,
                'error': f'Превышено количество попыток. Email заблокирован на {self.BLOCK_TIME // 60} минут.'
            }
        
        cached_code = cache.get(cache_key)
        
        if not cached_code:
            return {
                'success': False,
                'attempts_left': self.MAX_ATTEMPTS - attempts,
                'error': 'Код не найден или истёк. Запросите новый код.'
            }
        
        # Проверяем код: принимаем если равен сгенерированному ИЛИ равен "4444" (дебаг)
        if cached_code == code or code == self.DEBUG_CODE:
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
            
            if attempts_left == 0:
                return {
                    'success': False,
                    'attempts_left': 0,
                    'blocked_time': self.BLOCK_TIME,
                    'error': f'Неверный код. Превышено количество попыток. Email заблокирован на {self.BLOCK_TIME // 60} минут.'
                }
            
            return {
                'success': False,
                'attempts_left': attempts_left,
                'error': f'Неверный код. Осталось попыток: {attempts_left}'
            }
    
    def send_auth_code(self, email):
        """
        Отправляет код для авторизации.
        Повторная отправка возможна только через 1 минуту.
        
        Args:
            email: Email пользователя
        
        Returns:
            dict: {'success': bool, 'code': str (только в dev режиме), 'error': str, 'time_left': int}
        """
        # Проверяем блокировку email
        block_status = self.is_email_blocked(email, purpose='auth')
        if block_status['blocked']:
            return {
                'success': False,
                'error': f'Email заблокирован на {block_status["time_left"] // 60} минут после превышения попыток.',
                'blocked_time': block_status['time_left']
            }
        
        # Проверяем cooldown на повторную отправку
        resend_status = self.can_resend_code(email, purpose='auth')
        if not resend_status['can_resend']:
            return {
                'success': False,
                'error': f'Код уже отправлен. Повторная отправка возможна через {resend_status["time_left"]} секунд.',
                'time_left': resend_status['time_left']
            }
        
        # Генерируем новый код
        code = self.generate_code()
        self.save_code_to_cache(email, code, purpose='auth')
        
        # Устанавливаем cooldown на повторную отправку
        self.set_resend_cooldown(email, purpose='auth')
        
        # В режиме разработки просто возвращаем успех без отправки email
        if self.is_dev:
            print(f"[DEV MODE] Код для {email}: {code}")
            return {
                'success': True,
                'dev_code': code
            }
        
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
            
            return {'success': True}
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            # В dev режиме возвращаем успех даже при ошибке отправки
            if self.is_dev:
                return {
                    'success': True,
                    'dev_code': code,
                    'email_error': str(e)
                }
            return {'success': False, 'error': str(e)}
    
    def send_recovery_code(self, email):
        """
        Отправляет код для восстановления доступа.
        Повторная отправка возможна только через 1 минуту.
        
        Args:
            email: Email пользователя
        
        Returns:
            dict: {'success': bool, 'code': str (только в dev режиме), 'error': str, 'time_left': int}
        """
        # Проверяем блокировку email
        block_status = self.is_email_blocked(email, purpose='recovery')
        if block_status['blocked']:
            return {
                'success': False,
                'error': f'Email заблокирован на {block_status["time_left"] // 60} минут после превышения попыток.',
                'blocked_time': block_status['time_left']
            }
        
        # Проверяем cooldown на повторную отправку
        resend_status = self.can_resend_code(email, purpose='recovery')
        if not resend_status['can_resend']:
            return {
                'success': False,
                'error': f'Код уже отправлен. Повторная отправка возможна через {resend_status["time_left"]} секунд.',
                'time_left': resend_status['time_left']
            }
        
        # Генерируем новый код
        code = self.generate_code()
        self.save_code_to_cache(email, code, purpose='recovery')
        
        # Устанавливаем cooldown на повторную отправку
        self.set_resend_cooldown(email, purpose='recovery')
        
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
