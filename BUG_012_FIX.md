# БАГ-012: Управление видимостью организаций (is_active)

## Проблема

Не было возможности изменять поле `is_active` для организаций. Поле было в `read_only_fields`, что делало невозможным управление видимостью организаций через API.

## Описание

Администраторам необходима возможность скрывать/показывать организации в списке без удаления. Это полезно для:
- Временного скрытия организаций (например, на время ремонта)
- Модерации организаций
- Управления видимостью без потери данных

## Решение

### 1. Убрано поле is_active из read_only_fields

**Файл:** `organizations/serializers.py`

Поле `is_active` теперь можно изменять, но с ограничениями по правам доступа.

### 2. Добавлена валидация прав доступа

**Файл:** `organizations/serializers.py`

```python
def validate_is_active(self, value):
    """
    Проверяет права на изменение is_active.
    Только ADMIN может изменять видимость организации.
    """
    request = self.context.get('request')
    if not request:
        return value
    
    # Если это создание (нет instance), разрешаем
    if not self.instance:
        return value
    
    # Если значение не изменилось, разрешаем
    if self.instance.is_active == value:
        return value
    
    # Проверяем права: только ADMIN может изменять is_active
    if request.user.role != 'ADMIN':
        raise serializers.ValidationError(
            "Только администраторы могут изменять видимость организации"
        )
    
    return value
```

### 3. Добавлены специализированные endpoints

**Файл:** `organizations/views.py`

Добавлено 3 новых action для удобного управления видимостью:

#### toggle_active
```http
POST /api/organizations/{id}/toggle_active/
```
Переключает `is_active` на противоположное значение.

#### activate
```http
POST /api/organizations/{id}/activate/
```
Устанавливает `is_active = true`.

#### deactivate
```http
POST /api/organizations/{id}/deactivate/
```
Устанавливает `is_active = false`.

Все три endpoint доступны только для `ADMIN`.

## Способы использования

### Способ 1: Через PATCH запрос

```javascript
// Выключить видимость
await fetch('http://localhost:8000/api/organizations/5/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${admin_access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    is_active: false
  })
});

// Включить видимость
await fetch('http://localhost:8000/api/organizations/5/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${admin_access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    is_active: true
  })
});
```

### Способ 2: Через специализированные endpoints

```javascript
// Переключить видимость
await fetch('http://localhost:8000/api/organizations/5/toggle_active/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${admin_access_token}`
  }
});

// Включить видимость
await fetch('http://localhost:8000/api/organizations/5/activate/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${admin_access_token}`
  }
});

// Выключить видимость
await fetch('http://localhost:8000/api/organizations/5/deactivate/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${admin_access_token}`
  }
});
```

## Права доступа

| Действие | ADMIN | Владелец организации | CLIENT |
|----------|-------|---------------------|--------|
| Просмотр is_active | ✅ | ✅ | ✅ |
| Изменение is_active | ✅ | ❌ | ❌ |
| toggle_active | ✅ | ❌ | ❌ |
| activate | ✅ | ❌ | ❌ |
| deactivate | ✅ | ❌ | ❌ |

## Влияние на видимость

### Для клиентов (CLIENT)
Видят только организации с:
- `is_active = true`
- `organization_status = 'approved'`

### Для владельцев организаций
Видят свои организации независимо от `is_active`.

### Для администраторов (ADMIN)
Видят все организации независимо от `is_active`.

## Примеры ответов

### Успешное изменение через PATCH

```json
{
  "id": 5,
  "name": "Чистый Кузов",
  "shortName": "ЧК",
  "organizationStatus": "approved",
  "organizationDateApproved": "11/03/2026",
  "owner": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "owner_email": "org-owner@example.com",
  "city": 1,
  "address": "ул. Московское шоссе, 100",
  "phone": "+7 846 200-10-01",
  "email": "org@example.com",
  "description": "Мойка и детейлинг",
  "is_active": false,
  "created_at": "2026-03-11T09:15:00Z",
  "organizationType": "wash",
  "orgOgrn": "123456789012345",
  "orgInn": "123456789012",
  "orgKpp": "123456789",
  "wheelDiameters": [13, 14, 15, 16, 17, 18],
  "countServices": 3,
  "summaryPrice": "1500.00"
}
```

### Успешное изменение через toggle_active

```json
{
  "message": "Видимость организации выключена",
  "old_value": true,
  "new_value": false,
  "organization": {
    "id": 5,
    "name": "Чистый Кузов",
    "is_active": false,
    ...
  }
}
```

### Ошибка: попытка изменения не-администратором

```json
{
  "is_active": [
    "Только администраторы могут изменять видимость организации"
  ]
}
```

### Ошибка: попытка использования endpoint не-администратором

```json
{
  "error": "Только администраторы могут изменять видимость организации"
}
```

## Тестирование

### Тест 1: Администратор изменяет is_active через PATCH

```bash
# Выключить
curl -X PATCH http://localhost:8000/api/organizations/5/ \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Включить
curl -X PATCH http://localhost:8000/api/organizations/5/ \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

### Тест 2: Администратор использует специализированные endpoints

```bash
# Переключить
curl -X POST http://localhost:8000/api/organizations/5/toggle_active/ \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# Включить
curl -X POST http://localhost:8000/api/organizations/5/activate/ \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# Выключить
curl -X POST http://localhost:8000/api/organizations/5/deactivate/ \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"
```

### Тест 3: Владелец пытается изменить is_active (должна быть ошибка)

```bash
curl -X PATCH http://localhost:8000/api/organizations/5/ \
  -H "Authorization: Bearer ${OWNER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Ожидаемый результат: 400 Bad Request с сообщением об ошибке
```

### Тест 4: Клиент видит только активные организации

```bash
# Клиент запрашивает список организаций
curl http://localhost:8000/api/organizations/ \
  -H "Authorization: Bearer ${CLIENT_TOKEN}"

# Ожидаемый результат: только организации с is_active=true и status=approved
```

## Обратная совместимость

✅ Изменение обратно совместимо:
- Существующие запросы продолжают работать
- Поле `is_active` всегда возвращается в ответе
- Добавлены новые endpoints, старые не изменены
- Валидация применяется только при попытке изменения

## Файлы

### Измененные файлы
- `organizations/serializers.py` - добавлена валидация `is_active`
- `organizations/views.py` - добавлены 3 новых action
- `API_DOCUMENTATION.md` - добавлен раздел об управлении видимостью

### Новые файлы
- `BUG_012_FIX.md` - этот файл

## Статус

✅ Исправлено и протестировано

Администраторы теперь могут управлять видимостью организаций через API двумя способами: через PATCH запрос или через специализированные endpoints.
