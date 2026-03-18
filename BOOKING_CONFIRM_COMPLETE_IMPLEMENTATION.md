# Реализация подтверждения и завершения бронирований

## Обзор

Добавлены новые endpoints для управления жизненным циклом бронирований:
- `POST /api/bookings/{id}/confirm/` - подтверждение бронирования
- `POST /api/bookings/{id}/complete/` - завершение бронирования

## Переходы статусов

```
NEW → CONFIRMED (подтверждение организацией/админом)
NEW → CANCELLED (отмена клиентом/организацией/админом)

CONFIRMED → DONE (завершение организацией/админом)
CONFIRMED → CANCELLED (отмена клиентом/организацией/админом)

CANCELLED - финальный статус
DONE - финальный статус
```

## API Endpoints

### 1. Подтверждение бронирования

**Endpoint:** `POST /api/bookings/{id}/confirm/`

**Права доступа:**
- Владелец организации (для бронирований на свои услуги)
- Администратор

**Логика:**
- Можно подтвердить только бронирования со статусом `NEW`
- После подтверждения статус меняется на `CONFIRMED`

**Пример запроса:**
```http
POST /api/bookings/12/confirm/
Authorization: Bearer <owner_token>
```

**Успешный ответ (200):**
```json
{
  "message": "Бронирование успешно подтверждено",
  "confirmed_by": "organization",
  "old_status": "NEW",
  "booking": {
    "id": 12,
    "status": "CONFIRMED",
    "customerName": "Иван Петров",
    "dateTime": "30/03/2026 10:00",
    "carModel": "BMW X5",
    "serviceMethod": "Комплексная мойка",
    "duration": "60",
    "price": "1000.00"
  }
}
```

**Ошибки:**
- `403 Forbidden` - нет прав на подтверждение
- `400 Bad Request` - нельзя подтвердить бронирование с текущим статусом

### 2. Завершение бронирования

**Endpoint:** `POST /api/bookings/{id}/complete/`

**Права доступа:**
- Владелец организации (для бронирований на свои услуги)
- Администратор

**Логика:**
- Можно завершить только бронирования со статусом `CONFIRMED`
- После завершения статус меняется на `DONE`

**Пример запроса:**
```http
POST /api/bookings/13/complete/
Authorization: Bearer <owner_token>
```

**Успешный ответ (200):**
```json
{
  "message": "Бронирование успешно завершено",
  "completed_by": "organization",
  "old_status": "CONFIRMED",
  "booking": {
    "id": 13,
    "status": "DONE",
    "customerName": "Мария Сидорова",
    "dateTime": "30/03/2026 14:00",
    "carModel": "Toyota Camry",
    "serviceMethod": "Экспресс мойка",
    "duration": "30",
    "price": "500.00"
  }
}
```

**Ошибки:**
- `403 Forbidden` - нет прав на завершение
- `400 Bad Request` - нельзя завершить бронирование с текущим статусом

## Реализация

### Изменения в `bookings/views.py`

Добавлены два новых action-метода в `BookingViewSet`:

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
def confirm(self, request, pk=None):
    """
    Подтвердить бронирование.
    Доступно владельцу организации (брони на свои услуги) и администратору.
    """
    booking = self.get_object()
    
    # Проверка прав
    can_confirm = False
    confirmed_by = None
    
    if request.user.role == 'ADMIN':
        can_confirm = True
        confirmed_by = 'admin'
    elif booking.service.organization.owner == request.user:
        can_confirm = True
        confirmed_by = 'organization'
    
    if not can_confirm:
        return Response(
            {'error': 'У вас нет прав на подтверждение этого бронирования'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Проверка статуса
    if booking.status != 'NEW':
        return Response(
            {'error': f'Нельзя подтвердить бронирование со статусом {booking.status}. Подтверждать можно только новые бронирования (NEW).'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Подтверждаем
    old_status = booking.status
    booking.status = 'CONFIRMED'
    booking.save()
    
    serializer = self.get_serializer(booking)
    
    return Response({
        'message': 'Бронирование успешно подтверждено',
        'confirmed_by': confirmed_by,
        'old_status': old_status,
        'booking': serializer.data
    }, status=status.HTTP_200_OK)

@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
def complete(self, request, pk=None):
    """
    Завершить бронирование (отметить как выполненное).
    Доступно владельцу организации (брони на свои услуги) и администратору.
    """
    booking = self.get_object()
    
    # Проверка прав
    can_complete = False
    completed_by = None
    
    if request.user.role == 'ADMIN':
        can_complete = True
        completed_by = 'admin'
    elif booking.service.organization.owner == request.user:
        can_complete = True
        completed_by = 'organization'
    
    if not can_complete:
        return Response(
            {'error': 'У вас нет прав на завершение этого бронирования'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Проверка статуса
    if booking.status != 'CONFIRMED':
        return Response(
            {'error': f'Нельзя завершить бронирование со статусом {booking.status}. Завершать можно только подтвержденные бронирования (CONFIRMED).'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Завершаем
    old_status = booking.status
    booking.status = 'DONE'
    booking.save()
    
    serializer = self.get_serializer(booking)
    
    return Response({
        'message': 'Бронирование успешно завершено',
        'completed_by': completed_by,
        'old_status': old_status,
        'booking': serializer.data
    }, status=status.HTTP_200_OK)
```

## Тестирование

Создан тестовый скрипт `test_booking_status_transitions.py`, который проверяет:

1. ✅ Подтверждение бронирования (NEW → CONFIRMED)
2. ✅ Попытка повторного подтверждения (ошибка 400)
3. ✅ Завершение бронирования (CONFIRMED → DONE)
4. ✅ Попытка отменить завершенное бронирование (ошибка 400)
5. ✅ Полный цикл: NEW → CONFIRMED → DONE

### Результаты теста:

```
3. Тест: подтверждение бронирования организацией...
Статус: 200
✅ Бронирование подтверждено
   Сообщение: Бронирование успешно подтверждено
   Подтвердил: organization
   Старый статус: NEW
   Новый статус: CONFIRMED
   ✅ Статус корректно изменен на CONFIRMED

5. Тест: завершение бронирования организацией...
Статус: 200
✅ Бронирование завершено
   Сообщение: Бронирование успешно завершено
   Завершил: organization
   Старый статус: CONFIRMED
   Новый статус: DONE
   ✅ Статус корректно изменен на DONE

7. Тест полного цикла: NEW → CONFIRMED → DONE...
✅ Полный цикл пройден корректно: NEW → CONFIRMED → DONE

================================================================================
ВСЕ ТЕСТЫ ПРОЙДЕНЫ ✅
================================================================================
```

## Использование

### Типичный сценарий для организации:

1. Клиент создает бронирование (статус: NEW)
2. Организация получает уведомление о новом бронировании
3. Организация подтверждает бронирование: `POST /api/bookings/{id}/confirm/` (статус: CONFIRMED)
4. Клиент приезжает, услуга оказывается
5. Организация завершает бронирование: `POST /api/bookings/{id}/complete/` (статус: DONE)

### Альтернативный сценарий (отмена):

1. Клиент создает бронирование (статус: NEW)
2. Клиент или организация отменяет: `POST /api/bookings/{id}/cancel/` (статус: CANCELLED)

## Измененные файлы

- `bookings/views.py` - добавлены методы `confirm()` и `complete()`
- `API_DOCUMENTATION.md` - добавлена документация по новым endpoints
- `test_booking_status_transitions.py` - тестовый скрипт (новый)
- `BOOKING_CONFIRM_COMPLETE_IMPLEMENTATION.md` - документация (этот файл)

## Совместимость

Изменения полностью обратно совместимы:
- Существующие endpoints не изменены
- Добавлены только новые endpoints
- Модель `Booking` не изменена
- Существующие статусы остались прежними
