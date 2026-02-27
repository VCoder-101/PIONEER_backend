# Быстрый старт: Email авторизация

## Применение миграций

```bash
# Активировать виртуальное окружение
.\venv\Scripts\Activate.ps1

# Применить миграции
python manage.py migrate
```

## Тестирование

### 1. Запуск интерактивного теста

```bash
python test_email_service.py
```

Выберите:
- `1` - Отправка кода авторизации
- `2` - Отправка кода восстановления
- `3` - Полный цикл проверки кодов

### 2. Тест через API

**Шаг 1: Отправить код**
```bash
curl -X POST http://localhost:8000/api/users/auth/email/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "privacy_policy_accepted": true
  }'
```

**Ответ:**
```json
{
  "message": "Код отправлен на email",
  "email": "test@example.com",
  "dev_code": "4444"
}
```

**Шаг 2: Проверить код**
```bash
curl -X POST http://localhost:8000/api/users/auth/email/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "4444",
    "device_id": "test-device-123",
    "privacy_policy_accepted": true
  }'
```

**Ответ:**
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "role": "CLIENT",
    "is_new": true
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

## Важные детали

### Тестовый код
В режиме разработки (`DEBUG=True`) всегда используется код `4444`

### Срок жизни кода
Коды действительны 5 минут и удаляются после использования

### Ограничение попыток
Максимум 5 попыток на один код. После исчерпания попыток нужно запросить новый код.

### Email настройки
В режиме разработки (`DEBUG=True`) письма выводятся в консоль.
Для продакшена настройте SMTP в `.env`:
```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@example.com
```

## API Endpoints

### Авторизация
- `POST /api/users/auth/email/send-code/` - отправить код
- `POST /api/users/auth/email/verify-code/` - проверить код

### Восстановление доступа
- `POST /api/users/auth/email/recovery/send-code/` - отправить код восстановления
- `POST /api/users/auth/email/recovery/verify-code/` - проверить код восстановления

## Полная документация

См. `EMAIL_AUTH_DOCUMENTATION.md` для подробной информации.
