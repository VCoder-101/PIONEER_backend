# Исправление проблемы с Refresh Token

## 🔍 Проблема

**Симптом:** POST запрос на `/api/token/refresh/` возвращал 401 Unauthorized с сообщением "Authorization header missing (Bearer token required)".

**Причина:** 
1. **Refresh endpoint не был подключен** - отсутствовал маршрут `/api/token/refresh/` в `urls.py`
2. **Middleware блокировал запросы** - `JWTAuthorizationMiddleware` требовал Bearer token для ВСЕХ `/api/*` запросов, включая refresh

## 🛠 Исправление

### Измененные файлы:

#### 1. `pioneer_backend/urls.py`
```python
# Добавлен импорт
from rest_framework_simplejwt.views import TokenRefreshView

# Добавлен маршрут
path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
```

#### 2. `pioneer_backend/middleware.py`
```python
# Добавлен refresh endpoint в исключения
EXEMPT_PREFIXES = (
    "/admin/",
    "/api/users/auth/",
    "/api/token/refresh/",  # Новое исключение
)
```

#### 3. `API_DOCUMENTATION.md`
- Обновлена документация refresh endpoint
- Добавлены примеры использования
- Убрано упоминание о недоступности endpoint

## ✅ Результат

### Как теперь работает refresh flow:

1. **Получение токенов при авторизации:**
```http
POST /api/users/auth/verify-code/
{
  "email": "user@example.com",
  "code": "1234",
  "device_id": "web-chrome-01"
}
```

Ответ:
```json
{
  "jwt": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

2. **Обновление access token:**
```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ..."
}
```

Ответ:
```json
{
  "access": "eyJ..."
}
```

3. **Использование нового access token:**
```http
GET /api/users/me/
Authorization: Bearer <new_access_token>
```

### Ключевые особенности:

- ✅ **Refresh endpoint НЕ требует Bearer токена** в заголовке
- ✅ **Отправляется только refresh token** в теле запроса  
- ✅ **Возвращается новый access token**
- ✅ **Refresh token остается действительным** до истечения срока (30 дней)
- ✅ **Middleware корректно пропускает** refresh запросы

## 🧪 Тестирование

Создан тестовый скрипт `test_refresh_token.py` для проверки функциональности:

```bash
python test_refresh_token.py
```

Скрипт проверяет:
- Генерацию токенов
- Отправку refresh запроса
- Получение нового access token
- Использование нового токена для API запросов

## 📝 Простыми словами

**Что было:** Система выдавала refresh token, но использовать его было нельзя - сервер требовал access token даже для обновления токена (замкнутый круг).

**Что исправили:** Добавили специальный endpoint для refresh и исключили его из проверки токенов, чтобы можно было обновлять токены без access token.

**Как теперь работает:** Клиент может отправить refresh token и получить новый access token, когда старый истекает.