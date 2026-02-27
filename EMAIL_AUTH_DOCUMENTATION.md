# Документация: Авторизация и восстановление доступа через Email

## Обзор системы

Система использует email-коды подтверждения для:
- Авторизации новых и существующих пользователей
- Восстановления доступа к аккаунту

### Основные характеристики:
- **Код**: 4-значный (тестовый код в dev: `4444`)
- **Срок жизни**: 5 минут
- **Попытки**: 5 попыток, затем требуется новый код
- **Хранение**: Django cache (LocMemCache)
- **Email в dev**: Письма выводятся в консоль (console backend)
- **Email в prod**: Настраивается через .env (SMTP)

---

## API Эндпоинты

### 1. Отправка кода авторизации

**Endpoint**: `POST /api/users/auth/email/send-code/`

**Описание**: Отправляет 4-значный код на email для входа в систему.

**Request Body**:
```json
{
  "email": "user@example.com",
  "privacy_policy_accepted": true  // обязательно для новых пользователей
}
```

**Response (Success - 200)**:
```json
{
  "message": "Код отправлен на email",
  "email": "user@example.com",
  "dev_code": "4444"  // только в режиме разработки (DEBUG=True)
}
```

**Response (Error - 400)**:
```json
{
  "error": "Необходимо принять политику конфиденциальности"
}
```

---

### 2. Проверка кода авторизации

**Endpoint**: `POST /api/users/auth/email/verify-code/`

**Описание**: Проверяет код и авторизует пользователя.

**Request Body**:
```json
{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier",
  "privacy_policy_accepted": true  // для новых пользователей
}
```

**Response (Success - 200)**:
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "phone": null,
    "role": "CLIENT",
    "is_new": true
  },
  "session": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2025-03-29T12:00:00Z"
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Response (Error - 400)**:
```json
{
  "error": "Неверный код. Осталось попыток: 3",
  "attempts_left": 3
}
```

или

```json
{
  "error": "Превышено количество попыток. Запросите новый код.",
  "attempts_left": 0
}
```

---

### 3. Отправка кода восстановления

**Endpoint**: `POST /api/users/auth/email/recovery/send-code/`

**Описание**: Отправляет код для восстановления доступа к существующему аккаунту.

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response (Success - 200)**:
```json
{
  "message": "Код восстановления отправлен на email",
  "email": "user@example.com",
  "dev_code": "4444"  // только в режиме разработки
}
```

**Примечание**: Если пользователь не существует, система не раскрывает эту информацию (возвращает успешный ответ).

---

### 4. Проверка кода восстановления

**Endpoint**: `POST /api/users/auth/email/recovery/verify-code/`

**Описание**: Проверяет код восстановления и авторизует пользователя.

**Request Body**:
```json
{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier"
}
```

**Response (Success - 200)**:
```json
{
  "message": "Восстановление доступа успешно",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "phone": null,
    "role": "CLIENT",
    "is_new": false
  },
  "session": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2025-03-29T12:00:00Z"
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Response (Error - 404)**:
```json
{
  "error": "Пользователь не найден"
}
```

---

## Настройка

### 1. Переменные окружения (.env)

```env
# Email settings (настройте для продакшена)
# В режиме разработки (DEBUG=True) письма выводятся в консоль
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@example.com
```

### 2. Django Settings (pioneer_backend/settings.py)

```python
# Email settings
# В режиме разработки используем console backend (письма выводятся в консоль)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.example.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'noreply@example.com')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@pioneer.local')

# Cache settings (для кодов подтверждения)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 минут по умолчанию
    }
}
```

### 3. Миграции

```bash
# Активировать виртуальное окружение
.\venv\Scripts\Activate.ps1

# Создать миграции
python manage.py makemigrations users

# Применить миграции
python manage.py migrate
```

---

## Архитектура

### Компоненты системы:

1. **EmailVerificationService** (`users/email_service.py`)
   - Генерация кодов
   - Отправка email
   - Работа с кэшем
   - HTML-шаблоны писем

2. **Email Auth Views** (`users/email_auth_views.py`)
   - API эндпоинты
   - Валидация данных
   - Создание пользователей и сессий
   - Генерация JWT токенов

3. **User Model** (`users/models.py`)
   - Добавлено поле `email` (unique, nullable)
   - Индекс на поле email

### Хранение кодов:

```python
# Ключ в кэше
cache_key = f"email_code:{purpose}:{email}"
# purpose: 'auth' или 'recovery'

# TTL: 5 минут (300 секунд)
cache.set(cache_key, code, 300)
```

---

## Безопасность

### Реализованные меры:

1. **Криптографически безопасная генерация кодов**
   ```python
   code = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
   ```

2. **Одноразовые коды**
   - Код удаляется из кэша после успешной проверки

3. **Ограничение времени жизни**
   - Коды автоматически истекают через 5 минут

4. **Защита от перебора**
   - Коды хранятся в кэше, не в базе данных
   - Нет информации о количестве попыток

5. **Деактивация старых сессий**
   - При входе все предыдущие сессии пользователя деактивируются

6. **Не раскрывать информацию**
   - При восстановлении не сообщается, существует ли пользователь

---

## Тестирование

### Тестовый код в режиме разработки

При `DEBUG=True` всегда используется код `4444`:

```python
# В EmailVerificationService
TEST_CODE = "4444"
```

### Пример тестирования через curl:

```bash
# 1. Отправить код авторизации
curl -X POST http://localhost:8000/api/users/auth/email/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "privacy_policy_accepted": true
  }'

# 2. Проверить код
curl -X POST http://localhost:8000/api/users/auth/email/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "4444",
    "device_id": "test-device-123",
    "privacy_policy_accepted": true
  }'
```

### Тестирование отправки email:

```python
# Создайте файл test_email.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.email_service import email_verification_service

# Тест отправки кода авторизации
result = email_verification_service.send_auth_code('test@example.com')
print(f"Auth code result: {result}")

# Тест отправки кода восстановления
result = email_verification_service.send_recovery_code('test@example.com')
print(f"Recovery code result: {result}")
```

Запуск:
```bash
.\venv\Scripts\Activate.ps1
python test_email.py
```

---

## Frontend интеграция

### Пример JavaScript кода:

```javascript
// 1. Отправка кода авторизации
async function sendAuthCode(email) {
  const response = await fetch('/api/users/auth/email/send-code/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      privacy_policy_accepted: true
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    console.log('Код отправлен:', data.message);
    if (data.dev_code) {
      console.log('Dev код:', data.dev_code);
    }
  } else {
    console.error('Ошибка:', data.error);
  }
}

// 2. Проверка кода
async function verifyAuthCode(email, code, deviceId) {
  const response = await fetch('/api/users/auth/email/verify-code/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email,
      code: code,
      device_id: deviceId,
      privacy_policy_accepted: true
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    console.log('Авторизация успешна');
    console.log('User:', data.user);
    console.log('JWT Access:', data.jwt.access);
    console.log('JWT Refresh:', data.jwt.refresh);
    
    // Сохранить токены
    localStorage.setItem('access_token', data.jwt.access);
    localStorage.setItem('refresh_token', data.jwt.refresh);
    
    return data;
  } else {
    console.error('Ошибка:', data.error);
    throw new Error(data.error);
  }
}

// 3. Восстановление доступа
async function recoverAccess(email, code, deviceId) {
  // Отправить код восстановления
  await fetch('/api/users/auth/email/recovery/send-code/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email })
  });
  
  // Проверить код восстановления
  const response = await fetch('/api/users/auth/email/recovery/verify-code/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email,
      code: code,
      device_id: deviceId
    })
  });
  
  return await response.json();
}
```

---

## Troubleshooting

### Проблема: Email не отправляется

1. Проверьте настройки SMTP в `settings.py`
2. Убедитесь, что `EMAIL_HOST_PASSWORD` в `.env` корректен
3. Проверьте логи Django
4. Попробуйте отправить тестовое письмо через `test_email.py`

### Проблема: Код не принимается

1. Проверьте, что код не истек (5 минут)
2. Убедитесь, что код не был использован ранее
3. Проверьте правильность email (регистр не важен, email приводится к lowercase)

### Проблема: Кэш не работает

1. Убедитесь, что настройки CACHES в `settings.py` корректны
2. Проверьте, что Django cache работает:
   ```python
   from django.core.cache import cache
   cache.set('test', 'value', 60)
   print(cache.get('test'))  # должно вывести 'value'
   ```

---

## Производственное развертывание

### Изменения для продакшена:

1. **Отключить тестовый код**:
   ```python
   # В email_service.py
   def generate_code(self, use_test_code=None):
       if use_test_code is None:
           use_test_code = False  # Всегда False в продакшене
   ```

2. **Использовать Redis для кэша**:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

3. **Настроить rate limiting**:
   - Ограничить количество запросов на отправку кода (например, 3 в час)

4. **Мониторинг**:
   - Логировать все попытки авторизации
   - Отслеживать неудачные попытки

---

## Changelog

### v1.0.0 (2025-02-27)
- ✅ Реализована отправка кодов авторизации через email
- ✅ Реализована отправка кодов восстановления доступа
- ✅ Добавлено поле email в модель User
- ✅ В dev режиме письма выводятся в консоль (console backend)
- ✅ Коды хранятся в Django cache (TTL: 5 минут)
- ✅ Тестовый код для разработки: 4444
- ✅ HTML-шаблоны писем с брендингом Pioneer Study
- ✅ JWT токены для авторизованных пользователей
- ✅ Управление сессиями (одна активная сессия на устройство)
