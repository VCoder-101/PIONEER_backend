# Реализация функционала отмены бронирований

## Статус: ✅ ВЫПОЛНЕНО

## Что реализовано

### 1. Специальный endpoint для отмены бронирований

```http
POST /api/bookings/{id}/cancel/
Authorization: Bearer <access_token>
```

#### Права доступа:
- **Клиент** может отменить своё бронирование
- **Владелец организации** может отменить любое бронирование на услуги своей организации
- **Администратор** может отменить любое бронирование

#### Проверки при отмене:
- ✅ Проверка прав доступа (клиент/организация/администратор)
- ✅ Нельзя отменить уже отмененное бронирование (статус `CANCELLED`)
- ✅ Нельзя отменить завершенное бронирование (статус `DONE`)
- ✅ Логирование, кто отменил бронирование (`cancelled_by`)

#### Формат ответа:

```json
{
  "message": "Бронирование успешно отменено",
  "cancelled_by": "client",
  "old_status": "NEW",
  "booking": {
    "id": 42,
    "customerName": "Иван Петров",
    "dateTime": "20/03/2026 10:00",
    "carModel": "Lada Vesta",
    "serviceMethod": "Мойка",
    "duration": "60",
    "price": "500.00",
    "wheelDiameter": 16,
    "status": "CANCELLED",
    ...
  }
}
```

Поле `cancelled_by` может быть:
- `client` - отменено клиентом
- `organization` - отменено организацией
- `admin` - отменено администратором

### 2. Календарный формат данных

```http
GET /api/bookings/calendar/
Authorization: Bearer <access_token>
```

Возвращает бронирования в упрощенном формате для отображения в календаре (формат invoices):

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 0,
      "customerName": "Иван Петров",
      "dateTime": "10/01/2026 10:30",
      "carModel": "Lada Vesta",
      "serviceMethod": "Комплекс",
      "duration": "60",
      "price": "600.00"
    },
    {
      "id": 1,
      "customerName": "Иван Петров",
      "dateTime": "10/01/2026 11:30",
      "carModel": "Lada Granta",
      "serviceMethod": "Экспресс",
      "duration": "30",
      "price": "400.00"
    }
  ]
}
```

#### Особенности:
- ✅ Поддерживает все фильтры и сортировку основного списка
- ✅ Поддерживает пагинацию
- ✅ Упрощенный формат для фронтенда
- ✅ Учитывает права доступа (клиент видит свои, организация - свои услуги)

### 3. Обработка ошибок

#### 403 Forbidden - нет прав на отмену
```json
{
  "error": "У вас нет прав на отмену этого бронирования"
}
```

#### 400 Bad Request - уже отменено
```json
{
  "error": "Бронирование уже отменено"
}
```

#### 400 Bad Request - завершено
```json
{
  "error": "Нельзя отменить завершенное бронирование"
}
```

## Примеры использования

### Пример 1: Клиент отменяет своё бронирование

```bash
curl -X POST http://127.0.0.1:8000/api/bookings/42/cancel/ \
  -H "Authorization: Bearer <client_token>" \
  -H "Content-Type: application/json"
```

Ответ:
```json
{
  "message": "Бронирование успешно отменено",
  "cancelled_by": "client",
  "old_status": "NEW",
  "booking": { ... }
}
```

### Пример 2: Организация отменяет бронирование на свою услугу

```bash
curl -X POST http://127.0.0.1:8000/api/bookings/43/cancel/ \
  -H "Authorization: Bearer <owner_token>" \
  -H "Content-Type: application/json"
```

Ответ:
```json
{
  "message": "Бронирование успешно отменено",
  "cancelled_by": "organization",
  "old_status": "CONFIRMED",
  "booking": { ... }
}
```

### Пример 3: Получение календаря бронирований

```bash
curl -X GET "http://127.0.0.1:8000/api/bookings/calendar/?status=NEW,CONFIRMED&ordering=scheduled_at" \
  -H "Authorization: Bearer <token>"
```

Ответ в формате invoices для удобного отображения в календаре.

### Пример 4: Фильтрация календаря по дате

```bash
curl -X GET "http://127.0.0.1:8000/api/bookings/calendar/?scheduled_at__date=2026-03-25" \
  -H "Authorization: Bearer <token>"
```

## Технические детали

### Изменения в коде

#### bookings/views.py
- Добавлен импорт `status`, `action`, `Response` из DRF
- Добавлен импорт `InvoiceSerializer`
- Добавлен метод `cancel()` с декоратором `@action`
- Добавлен метод `calendar()` для календарного формата

#### bookings/serializers.py
- Уже существовал `InvoiceSerializer` для формата invoices

#### API_DOCUMENTATION.md
- Обновлена документация раздела Bookings API
- Добавлены примеры использования отмены бронирований
- Добавлено описание календарного формата

### Логика отмены

```python
@action(detail=True, methods=['post'])
def cancel(self, request, pk=None):
    booking = self.get_object()
    
    # Проверка прав
    can_cancel = False
    cancelled_by = None
    
    if request.user.role == 'ADMIN':
        can_cancel = True
        cancelled_by = 'admin'
    elif booking.user == request.user:
        can_cancel = True
        cancelled_by = 'client'
    elif booking.service.organization.owner == request.user:
        can_cancel = True
        cancelled_by = 'organization'
    
    if not can_cancel:
        return Response({'error': '...'}, status=403)
    
    # Проверка статуса
    if booking.status == 'CANCELLED':
        return Response({'error': '...'}, status=400)
    
    if booking.status == 'DONE':
        return Response({'error': '...'}, status=400)
    
    # Отмена
    old_status = booking.status
    booking.status = 'CANCELLED'
    booking.save()
    
    return Response({
        'message': 'Бронирование успешно отменено',
        'cancelled_by': cancelled_by,
        'old_status': old_status,
        'booking': serializer.data
    })
```

## Тестирование

Создан тестовый файл `test_booking_cancel.py` для проверки функционала:

```bash
python test_booking_cancel.py
```

Тесты проверяют:
- ✅ Права доступа на отмену
- ✅ Отмену клиентом
- ✅ Отмену организацией
- ✅ Попытку отменить уже отмененное бронирование
- ✅ Попытку отменить завершенное бронирование
- ✅ Календарный формат данных

## Что можно улучшить в будущем

### Уведомления
- Отправка email/push уведомлений при отмене бронирования
- Уведомление клиента, если организация отменила запись
- Уведомление организации, если клиент отменил запись

### Причина отмены
- Добавить поле `cancellation_reason` в модель Booking
- Позволить указывать причину отмены при вызове endpoint
- Сохранять, кто отменил (user_id) и когда (cancelled_at)

### История изменений
- Логирование всех изменений статуса бронирования
- Отдельная таблица BookingHistory для аудита

### Ограничения по времени
- Запретить отмену за N часов до начала услуги
- Разные правила для клиента и организации

### Штрафы и компенсации
- Система штрафов за позднюю отмену
- Компенсации клиенту при отмене организацией

## Заключение

Функционал отмены бронирований полностью реализован и готов к использованию. Система поддерживает:

✅ Отмену со стороны клиента
✅ Отмену со стороны организации
✅ Отмену администратором
✅ Проверку прав доступа
✅ Проверку статуса бронирования
✅ Календарный формат для фронтенда
✅ Логирование, кто отменил бронирование

API готов к интеграции с фронтендом.
