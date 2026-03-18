# БАГ-004: Исправление rate limiting при повторной отправке кода

**ID:** BUG-004 (TC-AUTH-04)  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

При повторной отправке кода на email в течение 1 минуты сервер возвращал 500 Internal Server Error вместо 429 Too Many Requests.

### Ошибка
```json
{
  "error": "Ошибка отправки email. Попробуйте позже."
}
```
Статус: 500 Internal Server Error

### Ожидаемое поведение
```json
{
  "error": "Код уже отправлен. Повторная отправка возможна через 60 секунд.",
  "time_left": 60
}
```
Статус: 429 Too Many Requests

## Решение

### Причина бага
В `users/email_auth_views.py` все ошибки от `email_verification_service.send_auth_code()` обрабатывались одинаково - возвращался статус 500. Не различались:
- Rate limiting (cooldown 60 секунд)
- Блокировка после превышения попыток
- Реальные ошибки отправки email

### Исправление

Создана helper функция `_handle_send_code_result()` для правильной обработки результатов:

```python
def _handle_send_code_result(result):
    """
    Обрабатывает результат отправки кода и возвращает Response с правильным статусом.
    """
    if result.get("success"):
        return None
    
    # Rate limiting - слишком частые запросы
    if "time_left" in result:
        return Response(
            {
                "error": result.get("error"),
                "time_left": result.get("time_left")
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    
    # Email заблокирован после превышения попыток
    elif "blocked_time" in result:
        return Response(
            {
                "error": result.get("error"),
                "blocked_time": result.get("blocked_time")
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    
    # Реальная ошибка отправки email
    else:
        return Response(
            {"error": "Ошибка отправки email. Попробуйте позже."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
```

Функция используется во всех эндпоинтах отправки кода:
- `send_register_email_code()`
- `send_email_auth_code()`
- `send_email_recovery_code()`
- `send_universal_auth_code()`

## Логика rate limiting

### Cooldown на повторную отправку
- **Период:** 60 секунд
- **Статус:** 429 Too Many Requests
- **Ответ:** `{"error": "...", "time_left": 60}`

### Блокировка после превышения попыток
- **Условие:** 5 неудачных попыток ввода кода
- **Период блокировки:** 420 секунд (7 минут)
- **Статус:** 429 Too Many Requests
- **Ответ:** `{"error": "...", "blocked_time": 420}`

### Реальная ошибка отправки email
- **Статус:** 500 Internal Server Error
- **Ответ:** `{"error": "Ошибка отправки email. Попробуйте позже."}`

## Тестирование

### Автоматический тест
```bash
# Быстрый тест (без ожидания cooldown)
python test_bug_004_rate_limiting.py --quick

# Полный тест (с ожиданием cooldown)
python test_bug_004_rate_limiting.py
```

### Результат
```
✅ ТЕСТ ПРОЙДЕН! Получен 429 Too Many Requests
Сообщение: Код уже отправлен. Повторная отправка возможна через 60 секунд.
Время ожидания: 60 секунд
```

### Что проверяет тест
1. ✅ Первая отправка кода возвращает 200
2. ✅ Немедленная повторная отправка возвращает 429 (не 500!)
3. ✅ Ответ содержит `time_left` с количеством секунд ожидания
4. ✅ После cooldown можно отправить код снова

## Измененные файлы

- `users/email_auth_views.py` - добавлена функция `_handle_send_code_result()` и обновлены все эндпоинты отправки кода

## Чеклист

- [x] Создана функция `_handle_send_code_result()`
- [x] Обновлены все эндпоинты отправки кода
- [x] Создан тест `test_bug_004_rate_limiting.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ТЕСТ ПРОЙДЕН
- [ ] Обновлена документация API

## Ручное тестирование

### 1. Первая отправка кода
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","privacy_policy_accepted":true}'
```

Ожидаемый ответ: **200 OK**
```json
{
  "message": "Код отправлен на email",
  "email": "test@example.com",
  "dev_code": "1234"
}
```

### 2. Немедленная повторная отправка
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","privacy_policy_accepted":true}'
```

Ожидаемый ответ: **429 Too Many Requests**
```json
{
  "error": "Код уже отправлен. Повторная отправка возможна через 60 секунд.",
  "time_left": 60
}
```

### 3. После ожидания 60 секунд
```bash
# Подождать 60 секунд, затем:
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","privacy_policy_accepted":true}'
```

Ожидаемый ответ: **200 OK** (код отправлен снова)

## Связанные документы

- `users/email_service.py` - EmailVerificationService с логикой rate limiting
- `users/email_auth_views.py` - эндпоинты авторизации
- API_DOCUMENTATION.md - документация API
