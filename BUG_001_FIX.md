# БАГ-001: Исправление инвалидации access токенов

## 🐛 Описание проблемы

**ID:** BUG-001  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено

### Симптом
После обновления access токена через refresh token, старый access токен оставался валидным в течение 30 минут (до истечения срока действия). Это создавало серьезную уязвимость безопасности.

### Шаги воспроизведения
1. Выполнить авторизацию, получить access token
2. Выполнить запрос `/api/users/auth/jwt/verify/` с текущим токеном
3. Сменить access token с помощью refresh token через `/api/token/refresh/`
4. Сразу после смены выполнить запрос `/api/users/auth/jwt/verify/` со старым access token

**Ожидаемый результат:** Токен должен быть аннулирован, API возвращает ошибку «Token is expired»  
**Фактический результат (до исправления):** Токен остается активным 30 минут

---

## ✅ Решение

### Архитектурный подход
JWT токены по своей природе stateless и не могут быть инвалидированы без дополнительной логики. Мы реализовали механизм привязки токенов к сессиям:

1. **Session ID в токене:** Каждый JWT токен содержит `session_id` в payload
2. **Проверка активности сессии:** При каждой верификации токена проверяется, активна ли связанная сессия
3. **Деактивация при обновлении:** При обновлении токена через refresh, старая сессия деактивируется

### Измененные файлы

#### 1. `users/authentication.py` (НОВЫЙ)
Кастомный JWT authentication класс с проверкой активности сессии:

```python
class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация с проверкой активности сессии.
    Инвалидирует токены, если сессия неактивна.
    """
    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)
        
        # Проверяем session_id в токене
        session_id = validated_token.get('session_id')
        if session_id:
            user_id = validated_token.get('user_id')
            try:
                session = UserSession.objects.get(id=session_id, user_id=user_id)
                if not session.is_active:
                    raise InvalidToken('Token is expired')
            except UserSession.DoesNotExist:
                raise InvalidToken('Token is expired')
        
        return validated_token
```

#### 2. `users/token_views.py` (НОВЫЙ)
Кастомный TokenRefreshView, который создает новую сессию при обновлении токена:

```python
class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    Кастомный TokenRefreshView, который:
    1. Деактивирует старую сессию
    2. Создает новую сессию
    3. Добавляет session_id в новые токены
    """
    def post(self, request, *args, **kwargs):
        # Деактивируем старую сессию
        # Создаем новую сессию
        # Генерируем новые токены с новым session_id
        ...
```

#### 3. `users/email_auth_views.py`
Обновлена функция `_create_session_and_jwt()` для добавления `session_id` в токены:

```python
def _create_session_and_jwt(user: User, request, device_id: str, message: str, is_new: bool):
    # ... создание сессии ...
    
    refresh = RefreshToken.for_user(user)
    # Добавляем session_id в payload токена для отслеживания
    refresh['session_id'] = str(session.id)
    access = refresh.access_token
    access['session_id'] = str(session.id)
    access = str(access)
    
    # ...
```

#### 4. `users/jwt_views.py`
Обновлена функция `verify_jwt_token()` для проверки активности сессии:

```python
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_jwt_token(request):
    # ... валидация токена ...
    
    # Проверяем session_id в токене
    session_id = token.get("session_id")
    if session_id:
        try:
            session = UserSession.objects.get(id=session_id, user_id=user_id)
            if not session.is_active:
                return Response(
                    {"valid": False, "error": "Token is expired"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except UserSession.DoesNotExist:
            return Response(
                {"valid": False, "error": "Token is expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    
    # ...
```

#### 5. `pioneer_backend/settings.py`
Обновлен `DEFAULT_AUTHENTICATION_CLASSES` для использования кастомного authentication:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.SessionAwareJWTAuthentication',  # Было: JWTAuthentication
        'rest_framework.authentication.SessionAuthentication',
    ],
    # ...
}
```

#### 6. `pioneer_backend/urls.py`
Обновлен endpoint для refresh токена:

```python
from users.token_views import SessionAwareTokenRefreshView

urlpatterns = [
    path('api/token/refresh/', SessionAwareTokenRefreshView.as_view(), name='token_refresh'),
    # ...
]
```

---

## 🔒 Как это работает

### Поток авторизации
1. Пользователь авторизуется → создается `UserSession` с `is_active=True`
2. Генерируются JWT токены с `session_id` в payload
3. При каждом запросе проверяется:
   - Валидность JWT (подпись, срок действия)
   - Активность сессии (`UserSession.is_active=True`)

### Поток обновления токена
1. Клиент отправляет refresh token + device_id на `/api/token/refresh/`
2. Сервер:
   - Извлекает `session_id` из старого refresh token
   - Деактивирует старую сессию (`is_active=False`)
   - Создает новую сессию с новым `session_id`
   - Генерирует новые токены с новым `session_id`
3. Старые токены становятся невалидными, т.к. их сессия неактивна

### Поток logout
1. Клиент отправляет `session_id` на `/api/users/auth/logout/`
2. Сервер деактивирует сессию (`is_active=False`)
3. Все токены, связанные с этой сессией, становятся невалидными

---

## 📝 Изменения в API

### `/api/token/refresh/` - Обновление токена

**Было:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Стало:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "device_id": "unique-device-identifier"
}
```

**Ответ:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "session": {
    "id": "uuid",
    "expires_at": "2026-04-17T12:00:00Z"
  }
}
```

**Важно:** Теперь `device_id` обязателен при обновлении токена!

---

## 🧪 Тестирование

Создан тестовый скрипт `test_bug_001_token_invalidation.py` для проверки исправления:

```bash
python test_bug_001_token_invalidation.py
```

Тест проверяет:
1. ✅ Авторизация и получение токенов
2. ✅ Валидность старого токена до обновления
3. ✅ Обновление токена через refresh
4. ✅ Инвалидация старого токена после обновления
5. ✅ Валидность нового токена

---

## 🔐 Безопасность

### Преимущества решения
- ✅ Старые токены инвалидируются мгновенно при обновлении
- ✅ Logout деактивирует все токены сессии
- ✅ Одна активная сессия на устройство
- ✅ Защита от кражи токенов (украденный токен инвалидируется при следующем refresh)

### Обратная совместимость
- ✅ Старые токены без `session_id` продолжают работать (для плавной миграции)
- ✅ Все новые токены автоматически получают `session_id`
- ⚠️ Клиенты должны передавать `device_id` при refresh (обязательное поле)

---

## 📊 Влияние на производительность

- **Дополнительный запрос к БД:** При каждой верификации токена выполняется запрос к `UserSession`
- **Оптимизация:** Добавлен индекс на `UserSession.id` и `UserSession.is_active`
- **Кэширование:** Можно добавить Redis кэш для активных сессий (опционально)

---

## 🚀 Развертывание

### Миграции
Не требуются - используются существующие модели `User` и `UserSession`.

### Обновление клиентов
Клиенты должны обновить логику refresh токена:

**Было:**
```javascript
POST /api/token/refresh/
{ "refresh": refreshToken }
```

**Стало:**
```javascript
POST /api/token/refresh/
{ 
  "refresh": refreshToken,
  "device_id": deviceId  // ОБЯЗАТЕЛЬНО!
}
```

---

## ✅ Чеклист развертывания

- [x] Создан `users/authentication.py`
- [x] Создан `users/token_views.py`
- [x] Обновлен `users/email_auth_views.py`
- [x] Обновлен `users/jwt_views.py`
- [x] Обновлен `pioneer_backend/settings.py`
- [x] Обновлен `pioneer_backend/urls.py`
- [x] Создан тест `test_bug_001_token_invalidation.py`
- [x] Запущен тест для проверки - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
- [ ] Обновить документацию API
- [ ] Уведомить frontend команду об изменениях

---

## 📚 Дополнительные материалы

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [djangorestframework-simplejwt Documentation](https://django-rest-framework-simplejwt.readthedocs.io/)
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
