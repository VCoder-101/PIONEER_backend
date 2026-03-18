# Сводка изменений API (Март 2026)

## Breaking Changes

### БАГ-001: Refresh Token
**Endpoint:** `POST /api/token/refresh/`

**Изменение:** Теперь требует обязательное поле `device_id`

**Было:**
```json
{
  "refresh": "eyJ..."
}
```

**Стало:**
```json
{
  "refresh": "eyJ...",
  "device_id": "unique-device-identifier"
}
```

**Поведение:** Старый access token теперь инвалидируется немедленно при обновлении.

## Исправления багов

### БАГ-002: Создание организации
- CLIENT теперь может создавать организации
- Поля `organizationStatus` и `owner` теперь read-only

### БАГ-003: Создание бронирования
- Поле `user` НЕ требуется (устанавливается автоматически)
- Поддержка camelCase и snake_case
- Поля `dateTime` и `carModel` опциональны

### БАГ-004: Rate Limiting
- Повторная отправка кода теперь возвращает 429 вместо 500

### БАГ-005: Статус бронирования
- Поле `status` теперь всегда возвращается в ответе

### БАГ-006: Данные организации
- Добавлены поля `countServices` и `summaryPrice` в ответ

### БАГ-009: Уникальность организаций
- Добавлена проверка уникальности названия организации (case-insensitive)

### БАГ-010: Создание услуг
- Услуги можно создавать только для одобренных организаций (status='approved')
- При попытке создать услугу для неодобренной организации возвращается 403

### БАГ-011: Календарь бронирований
- Добавлено поле `bookingStatus` в `/api/bookings/calendar/`
- Значения: `active` (NEW, CONFIRMED) или `archived` (CANCELLED, DONE)

## Новые endpoints

### Подтверждение бронирования
**Endpoint:** `POST /api/bookings/{id}/confirm/`

**Доступ:** Организация (владелец), Администратор

**Переход:** NEW → CONFIRMED

**Пример ответа:**
```json
{
  "message": "Бронирование успешно подтверждено",
  "confirmed_by": "organization",
  "old_status": "NEW",
  "booking": { ... }
}
```

### Завершение бронирования
**Endpoint:** `POST /api/bookings/{id}/complete/`

**Доступ:** Организация (владелец), Администратор

**Переход:** CONFIRMED → DONE

**Пример ответа:**
```json
{
  "message": "Бронирование успешно завершено",
  "completed_by": "organization",
  "old_status": "CONFIRMED",
  "booking": { ... }
}
```

## Переходы статусов бронирований

```
NEW → CONFIRMED (confirm)
NEW → CANCELLED (cancel)

CONFIRMED → DONE (complete)
CONFIRMED → CANCELLED (cancel)

CANCELLED - финальный
DONE - финальный
```

## Изменения в форматах ответов

### Календарь бронирований (БАГ-011)

**Было:**
```json
{
  "id": 10,
  "customerName": "Иван Петров",
  "dateTime": "25/03/2026 10:00",
  "carModel": "BMW X5",
  "serviceMethod": "Мойка",
  "duration": "60",
  "price": "1000.00",
  "status": "NEW"
}
```

**Стало:**
```json
{
  "id": 10,
  "customerName": "Иван Петров",
  "dateTime": "25/03/2026 10:00",
  "carModel": "BMW X5",
  "serviceMethod": "Мойка",
  "duration": "60",
  "price": "1000.00",
  "status": "NEW",
  "bookingStatus": "active"
}
```

### Организация (БАГ-006)

Добавлены поля:
```json
{
  ...
  "countServices": 5,
  "summaryPrice": "5000.00"
}
```

## Рекомендации по миграции

### 1. Обновите refresh token запросы
Добавьте `device_id` во все запросы к `/api/token/refresh/`

### 2. Обновите создание бронирований
Удалите поле `user` из запросов создания бронирований

### 3. Используйте bookingStatus
Для фильтрации активных/архивных бронирований используйте новое поле `bookingStatus`

### 4. Проверьте статус организации
Перед созданием услуги убедитесь, что организация одобрена (status='approved')

### 5. Используйте новые endpoints
Для управления бронированиями используйте:
- `POST /api/bookings/{id}/confirm/` - подтверждение
- `POST /api/bookings/{id}/complete/` - завершение
- `POST /api/bookings/{id}/cancel/` - отмена

## Совместимость

Все изменения обратно совместимы, кроме:
- **БАГ-001:** Требуется `device_id` в refresh token запросах

Остальные изменения добавляют новые поля или endpoints, не ломая существующую функциональность.
