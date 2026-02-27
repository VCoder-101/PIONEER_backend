# Сводка: Настройка Email системы

## Текущее состояние

### Режим разработки (DEBUG=True)
✅ Письма выводятся в консоль (console backend)
✅ Тестовый код: `4444`
✅ Все работает без настройки SMTP

### Для продакшена (DEBUG=False)

Необходимо настроить SMTP в `.env`:

```env
DEBUG=False

# Email settings
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@example.com
```

## Тестирование

### Быстрый тест
```bash
python test_send_email.py
```

Письмо будет выведено в консоль с кодом `4444`.

### Полный тест
```bash
python test_email_service.py
```

Интерактивное меню для тестирования всех функций.

## API Endpoints

### Авторизация
```bash
# Отправить код
POST /api/users/auth/email/send-code/
{
  "email": "user@example.com",
  "privacy_policy_accepted": true
}

# Проверить код
POST /api/users/auth/email/verify-code/
{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "device-123",
  "privacy_policy_accepted": true
}
```

### Восстановление доступа
```bash
# Отправить код восстановления
POST /api/users/auth/email/recovery/send-code/
{
  "email": "user@example.com"
}

# Проверить код восстановления
POST /api/users/auth/email/recovery/verify-code/
{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "device-123"
}
```

## Важно

- В dev режиме письма НЕ отправляются реально, а выводятся в консоль
- Код всегда `4444` в dev режиме
- Коды хранятся в cache 5 минут
- После использования код удаляется автоматически

## Документация

- `EMAIL_AUTH_DOCUMENTATION.md` - полная документация API
- `EMAIL_AUTH_QUICKSTART.md` - быстрый старт
- `CHANGELOG.md` - история изменений
