# БАГ-007: Исправление отображения статуса бронирования в календаре

**ID:** BUG-007  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

При запросе `/api/bookings/calendar/` отмененные бронирования не помечались статусом. Поле `status` отсутствовало в ответе, из-за чего невозможно было отличить активные бронирования от отмененных.

### Причина
В `InvoiceSerializer` (используется для календарного представления) отсутствовало поле `status`.

```python
# До исправления
class InvoiceSerializer(serializers.ModelSerializer):
    customerName = serializers.CharField(source='user.name', read_only=True)
    dateTime = serializers.DateTimeField(source='scheduled_at', format='%d/%m/%Y %H:%M', read_only=True)
    carModel = serializers.CharField(source='car_model', read_only=True)
    serviceMethod = serializers.CharField(source='service.title', read_only=True)
    duration = serializers.CharField(source='service.duration', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    # status отсутствует!

    class Meta:
        model = Booking
        fields = ['id', 'customerName', 'dateTime', 'carModel', 'serviceMethod', 'duration', 'price']
```

## Решение

Добавлено поле `status` в `InvoiceSerializer`:

```python
# После исправления
class InvoiceSerializer(serializers.ModelSerializer):
    customerName = serializers.CharField(source='user.name', read_only=True)
    dateTime = serializers.DateTimeField(source='scheduled_at', format='%d/%m/%Y %H:%M', read_only=True)
    carModel = serializers.CharField(source='car_model', read_only=True)
    serviceMethod = serializers.CharField(source='service.title', read_only=True)
    duration = serializers.CharField(source='service.duration', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)  # Добавлено!

    class Meta:
        model = Booking
        fields = ['id', 'customerName', 'dateTime', 'carModel', 'serviceMethod', 'duration', 'price', 'status']
```

## Статусы бронирования

Модель `Booking` поддерживает следующие статусы:

- `NEW` - Новая (только создана)
- `CONFIRMED` - Подтверждена
- `CANCELLED` - Отменена
- `DONE` - Завершена

## Пример ответа API

### GET /api/bookings/calendar/

**До исправления:**
```json
[
  {
    "id": 1,
    "customerName": "John Doe",
    "dateTime": "20/03/2026 10:00",
    "carModel": "Toyota Camry",
    "serviceMethod": "Car Wash",
    "duration": 60,
    "price": "1000.00"
    // status отсутствует!
  }
]
```

**После исправления:**
```json
[
  {
    "id": 1,
    "customerName": "John Doe",
    "dateTime": "20/03/2026 10:00",
    "carModel": "Toyota Camry",
    "serviceMethod": "Car Wash",
    "duration": 60,
    "price": "1000.00",
    "status": "NEW"
  },
  {
    "id": 2,
    "customerName": "Jane Smith",
    "dateTime": "21/03/2026 14:00",
    "carModel": "Honda Civic",
    "serviceMethod": "Tire Change",
    "duration": 90,
    "price": "1500.00",
    "status": "CANCELLED"
  }
]
```

## Тестирование

### Автоматический тест
```bash
python test_bug_007_booking_status.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-007 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Создание бронирования со статусом NEW
2. ✅ Поле status присутствует в календаре
3. ✅ Отмена бронирования
4. ✅ Статус CANCELLED корректно отображается в календаре

## Использование на фронтенде

Теперь можно фильтровать и отображать бронирования по статусу:

```javascript
// Получить все бронирования
const response = await fetch('/api/bookings/calendar/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const bookings = await response.json();

// Фильтровать активные бронирования
const activeBookings = bookings.filter(b => 
  b.status !== 'CANCELLED' && b.status !== 'DONE'
);

// Фильтровать отмененные бронирования
const cancelledBookings = bookings.filter(b => 
  b.status === 'CANCELLED'
);

// Отображать с разными стилями
bookings.forEach(booking => {
  const className = booking.status === 'CANCELLED' 
    ? 'booking-cancelled' 
    : 'booking-active';
  
  // Рендер с соответствующим классом
});
```

## Измененные файлы

- `bookings/serializers.py` - добавлено поле `status` в `InvoiceSerializer`

## Чеклист

- [x] Обновлен `bookings/serializers.py`
- [x] Создан тест `test_bug_007_booking_status.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API
- [ ] Уведомлен frontend о новом поле

## Связанные документы

- `bookings/models.py` - модель Booking со статусами
- `bookings/views.py` - BookingViewSet с методом cancel
- API_DOCUMENTATION.md - документация API
