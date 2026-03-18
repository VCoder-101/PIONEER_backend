# БАГ-005: Исправление permissions для редактирования услуг

**ID:** BUG-005  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

Владелец организации не мог редактировать услуги своей организации. При попытке PATCH запроса получал 403 Forbidden.

### Ошибка из логов
```
[14/Mar/2026 15:05:52] "PATCH /api/services/2/ HTTP/1.1" 403 130
Forbidden: /api/services/2/
```

### Причина
В `services/permissions.py` и `services/views.py` проверялась несуществующая роль `ORGANIZATION`:

```python
# Неправильно
if request.user.role == 'ORGANIZATION':
    return True
```

Но в системе существуют только две роли:
- `ADMIN` - администратор
- `CLIENT` - клиент

Владелец организации - это `CLIENT` с организацией (связь через `user.organizations`).

## Решение

### Исправлен `services/permissions.py`

**Было:**
```python
# Владелец может создавать и читать
if request.user.role == 'ORGANIZATION':
    return True
```

**Стало:**
```python
# Владелец организации (CLIENT с организацией) может создавать и управлять
if hasattr(request.user, 'organizations') and request.user.organizations.exists():
    return True
```

### Исправлен `services/views.py`

**ServiceViewSet.get_queryset():**
```python
# Было
elif user.role == 'CLIENT':
    return Service.objects.filter(is_active=True, status='active')
else:
    return Service.objects.filter(organization__owner=user)

# Стало
else:
    user_organizations = user.organizations.all()
    if user_organizations.exists():
        # Владелец организации
        return Service.objects.filter(organization__owner=user)
    else:
        # Обычный клиент
        return Service.objects.filter(is_active=True, status='active')
```

**ServiceItemViewSet.get_queryset()** - аналогичные изменения.

## Логика permissions после исправления

### Создание услуги (POST /api/services/)
- ✅ **ADMIN** - может создать для любой организации
- ✅ **CLIENT с организацией** - может создать для своей организации
- ❌ **CLIENT без организации** - не может создавать услуги

### Редактирование услуги (PATCH /api/services/{id}/)
- ✅ **ADMIN** - может редактировать любую услугу
- ✅ **Владелец организации** - может редактировать услуги своей организации
- ❌ **Другие пользователи** - не могут редактировать чужие услуги

### Чтение услуг (GET /api/services/)
- ✅ **ADMIN** - видит все услуги
- ✅ **Владелец организации** - видит все свои услуги (включая ghost)
- ✅ **CLIENT без организации** - видит только активные услуги (status='active')

## Дополнительная проблема: Trailing slash

В логах также была ошибка:
```
RuntimeError: You called this URL via PATCH, but the URL doesn't end in a slash
```

### Решение
Всегда используйте trailing slash в URL:
- ✅ Правильно: `/api/services/2/`
- ❌ Неправильно: `/api/services/2`

Django требует trailing slash для PATCH/PUT запросов при `APPEND_SLASH=True` (по умолчанию).

## Тестирование

### Автоматический тест
```bash
python test_bug_005_service_permissions.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-005 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Авторизация под клиентом
2. ✅ Создание организации
3. ✅ Создание услуги владельцем организации
4. ✅ Редактирование услуги владельцем (PATCH)
5. ✅ Видимость услуги владельцу

## Измененные файлы

- `services/permissions.py` - обновлен `IsServiceOwner`
- `services/views.py` - обновлены `ServiceViewSet.get_queryset()` и `ServiceItemViewSet.get_queryset()`

## Чеклист

- [x] Обновлен `services/permissions.py`
- [x] Обновлен `services/views.py`
- [x] Создан тест `test_bug_005_service_permissions.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API

## Ручное тестирование

### 1. Создание организации
```bash
curl -X POST http://127.0.0.1:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "name": "My Organization",
    "shortName": "MO",
    "organizationType": "wash",
    "city": 1,
    "address": "Test Address",
    "phone": "+7 900 000-00-00",
    "email": "org@example.com",
    "orgInn": "123456789012",
    "orgOgrn": "123456789012345",
    "orgKpp": "123456789"
  }'
```

### 2. Создание услуги
```bash
curl -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "organization": 1,
    "title": "Car Wash",
    "description": "Full car wash service",
    "price": "1000.00",
    "duration": 60,
    "status": "active"
  }'
```

### 3. Редактирование услуги
```bash
curl -X PATCH http://127.0.0.1:8000/api/services/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "title": "Premium Car Wash",
    "price": "1500.00"
  }'
```

Ожидаемый ответ: **200 OK** (не 403!)

## Связанные документы

- `services/models.py` - модели Service и ServiceItem
- `organizations/models.py` - модель Organization
- `users/models.py` - модель User с ролями
