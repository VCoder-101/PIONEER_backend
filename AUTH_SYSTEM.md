# Система аутентификации Pioneer Backend

## Обзор

Аутентификация по номеру телефона через SMS-код (без пароля).

## Особенности

- ✅ Регистрация и вход через SMS-код
- ✅ Одна активная сессия на одном устройстве
- ✅ TTL SMS-кода: 5 минут
- ✅ Максимум 3 попытки ввода кода
- ✅ Защита от спама (1 минута между запросами)
- ✅ Согласие с политикой конфиденциальности

## Модели

### User
```python
- id (UUID)
- phone (unique, indexed)
- role (ADMIN / ORGANIZATION / CLIENT)
- is_active
- privacy_policy_accepted_at
- current_device_id
- current_session_id
- created_at
- updated_at
- last_login_at
```

### AuthCode
```python
- id (UUID)
- phone (indexed)
- code (6 цифр)
- attempts_left (default: 3)
- is_used
- created_at (indexed)
- expires_at (indexed, TTL: 5 минут)
```

### UserSession
```python
- id (UUID)
- user (FK)
- device_id (indexed)
- ip_address
- user_agent
- created_at (indexed)
- expires_at (indexed, TTL: 30 дней)
- is_active (indexed)
```

## API Endpoints

### 1. Отправить SMS-код

```http
POST /api/users/auth/send-code/
Content-Type: application/json

{
  "phone": "8 (999) 123 45 67",
  "privacy_policy_accepted": true  // обязательно для новых пользователей
}
```

**Ответ (200 OK):**
```json
{
  "message": "SMS-код отправлен",
  "phone": "89991234567",
  "code_id": "uuid",
  "dev_code": "123456"  // ТОЛЬКО ДЛЯ РАЗРАБОТКИ!
}
```

**Ошибки:**
- `400` - Номер телефона обязателен
- `400` - Необходимо принять политику конфиденциальности
- `429` - Код уже отправлен. Подождите 1 минуту.

### 2. Проверить SMS-код и авторизоваться

```http
POST /api/users/auth/verify-code/
Content-Type: application/json

{
  "phone": "8 (999) 123 45 67",
  "code": "123456",
  "device_id": "unique-device-identifier",
  "privacy_policy_accepted": true  // для новых пользователей
}
```

**Ответ (200 OK):**
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "uuid",
    "phone": "89991234567",
    "role": "CLIENT",
    "is_new": true
  },
  "session": {
    "id": "uuid",
    "expires_at": "2026-03-20T12:00:00Z"
  }
}
```

**Ошибки:**
- `400` - Необходимы: phone, code, device_id
- `400` - Код не найден или истёк. Запросите новый код.
- `400` - Превышено количество попыток. Запросите новый код.
- `400` - Неверный код (+ attempts_left)

### 3. Выйти из системы

```http
POST /api/users/auth/logout/
Content-Type: application/json
Authorization: Bearer <token>

{
  "session_id": "uuid"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Выход выполнен"
}
```

## Поток аутентификации

### Регистрация нового пользователя

```
1. Пользователь вводит номер телефона
2. Ставит чекбокс "Принимаю политику конфиденциальности"
3. Нажимает "Получить код"
   → POST /api/users/auth/send-code/
   {
     "phone": "8 (999) 123 45 67",
     "privacy_policy_accepted": true
   }

4. Получает SMS с кодом (TTL: 5 минут)

5. Вводит код
   → POST /api/users/auth/verify-code/
   {
     "phone": "8 (999) 123 45 67",
     "code": "123456",
     "device_id": "device-uuid",
     "privacy_policy_accepted": true
   }

6. Получает session_id и user_id
7. Сохраняет session_id для последующих запросов
```

### Вход существующего пользователя

```
1. Пользователь вводит номер телефона
2. Нажимает "Получить код"
   → POST /api/users/auth/send-code/
   {
     "phone": "8 (999) 123 45 67"
   }

3. Получает SMS с кодом

4. Вводит код
   → POST /api/users/auth/verify-code/
   {
     "phone": "8 (999) 123 45 67",
     "code": "123456",
     "device_id": "device-uuid"
   }

5. Получает session_id
6. Если был залогинен на другом устройстве - старая сессия деактивируется
```

## Безопасность

### Защита от брутфорса
- Максимум 3 попытки ввода кода
- После 3 неудачных попыток - код становится недействительным
- Требуется запросить новый код

### Защита от спама
- Минимум 1 минута между запросами кода на один номер
- Старые неиспользованные коды деактивируются при запросе нового

### Одна активная сессия
- При логине на новом устройстве - старая сессия деактивируется
- Пользователь может быть авторизован только на одном устройстве

### TTL
- SMS-код: 5 минут
- Сессия: 30 дней

## Интеграция с SMS-провайдером

В файле `users/auth_views.py` есть TODO для интеграции:

```python
# TODO: Интеграция с SMS-провайдером
# send_sms(phone_clean, f"Ваш код: {code}")
```

Рекомендуемые провайдеры:
- Twilio
- SMS.ru
- SMSC.ru
- MessageBird

## Режим разработки

В режиме разработки endpoint `/api/users/auth/send-code/` возвращает код в ответе:

```json
{
  "dev_code": "123456"  // УБРАТЬ В ПРОДАКШЕНЕ!
}
```

**ВАЖНО:** Удалить это поле перед деплоем в продакшен!

## Миграция данных

Если у вас уже есть пользователи с email/password:

1. Создать скрипт миграции
2. Для каждого пользователя:
   - Запросить номер телефона
   - Отправить SMS с кодом подтверждения
   - После подтверждения - обновить запись

## Тестирование

### Тестовые номера (для разработки)

Можно добавить тестовые номера с фиксированным кодом:

```python
TEST_PHONES = {
    '89991234567': '111111',
    '89991234568': '222222',
}

if phone_clean in TEST_PHONES:
    code = TEST_PHONES[phone_clean]
```

### Примеры запросов (curl)

```bash
# 1. Отправить код
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 123 45 67",
    "privacy_policy_accepted": true
  }'

# 2. Проверить код
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 123 45 67",
    "code": "123456",
    "device_id": "test-device-123"
  }'

# 3. Выйти
curl -X POST http://127.0.0.1:8000/api/users/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "session_id": "uuid"
  }'
```

## Мониторинг

Рекомендуется отслеживать:
- Количество отправленных SMS в день
- Процент успешных авторизаций
- Количество неудачных попыток ввода кода
- Количество активных сессий

## Стоимость

SMS-коды - платная услуга. Примерная стоимость:
- Россия: 1-3 руб за SMS
- При 1000 пользователей в день: 1000-3000 руб/день

Рекомендации по оптимизации:
- Увеличить TTL кода до 10 минут
- Добавить капчу перед отправкой кода
- Ограничить количество запросов с одного IP
