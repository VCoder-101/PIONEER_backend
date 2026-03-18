# БАГ-011: Календарь не возвращает статус бронирования (active/archived)

## Описание проблемы
Endpoint `/api/bookings/calendar/` возвращал только поле `status` (NEW, CONFIRMED, CANCELLED, DONE), но не возвращал вычисляемое поле `bookingStatus`, которое показывает, является ли бронирование активным или архивным.

Фронтенду требуется поле `bookingStatus` для фильтрации и отображения бронирований:
- `active` - активные бронирования (NEW, CONFIRMED)
- `archived` - завершенные/отмененные бронирования (CANCELLED, DONE)

## Причина
В сериализаторе `InvoiceSerializer` отсутствовало поле `bookingStatus`, которое вычисляет статус на основе поля `status`.

## Решение

### Обновлен `bookings/serializers.py`
Добавлено вычисляемое поле `bookingStatus` в `InvoiceSerializer`:

```python
class InvoiceSerializer(serializers.ModelSerializer):
    """Сериализатор для формата invoices (упрощенный)"""
    customerName = serializers.CharField(source='user.name', read_only=True)
    dateTime = serializers.DateTimeField(source='scheduled_at', format='%d/%m/%Y %H:%M', read_only=True)
    carModel = serializers.CharField(source='car_model', read_only=True)
    serviceMethod = serializers.CharField(source='service.title', read_only=True)
    duration = serializers.CharField(source='service.duration', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    bookingStatus = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'customerName', 'dateTime', 'carModel', 'serviceMethod', 'duration', 'price', 'status', 'bookingStatus']
    
    def get_bookingStatus(self, obj):
        """
        Определяет статус бронирования для календаря:
        - active: NEW, CONFIRMED
        - archived: CANCELLED, DONE
        """
        if obj.status in ['NEW', 'CONFIRMED']:
            return 'active'
        elif obj.status in ['CANCELLED', 'DONE']:
            return 'archived'
        return 'active'  # По умолчанию
```

## Тестирование
Созданы тестовые скрипты:
1. `test_bug_011_calendar_status.py` - базовая проверка наличия поля
2. `test_bug_011_calendar_status_full.py` - полная проверка всех статусов

### Результаты теста:
```
5. Проверка статусов...
✅ ID 11:
   status: NEW (ожидалось: NEW) ✅
   bookingStatus: active (ожидалось: active) ✅
✅ ID 12:
   status: CONFIRMED (ожидалось: CONFIRMED) ✅
   bookingStatus: active (ожидалось: active) ✅
✅ ID 13:
   status: CANCELLED (ожидалось: CANCELLED) ✅
   bookingStatus: archived (ожидалось: archived) ✅

================================================================================
ТЕСТ ПОЛНОСТЬЮ ПРОЙДЕН ✅
Все статусы бронирований корректно отображаются в календаре:
  - NEW → bookingStatus: active ✅
  - CONFIRMED → bookingStatus: active ✅
  - CANCELLED → bookingStatus: archived ✅
================================================================================
```

## Пример ответа календаря

### До исправления:
```json
{
  "id": 10,
  "customerName": "Test User",
  "dateTime": "25/03/2026 10:00",
  "carModel": "Test Car",
  "serviceMethod": "Мойка",
  "duration": "60",
  "price": "1000.00",
  "status": "NEW"
}
```

### После исправления:
```json
{
  "id": 10,
  "customerName": "Test User",
  "dateTime": "25/03/2026 10:00",
  "carModel": "Test Car",
  "serviceMethod": "Мойка",
  "duration": "60",
  "price": "1000.00",
  "status": "NEW",
  "bookingStatus": "active"
}
```

## Результат
Теперь endpoint `/api/bookings/calendar/` возвращает поле `bookingStatus`, которое позволяет фронтенду:
- Фильтровать активные и архивные бронирования
- Отображать бронирования в разных вкладках/секциях
- Применять разные стили для активных и архивных записей

## Логика определения статуса
- `active` - бронирования, которые еще не завершены:
  - NEW - новое бронирование
  - CONFIRMED - подтвержденное бронирование
  
- `archived` - завершенные бронирования:
  - CANCELLED - отмененное бронирование
  - DONE - выполненное бронирование

## Измененные файлы
- `bookings/serializers.py` - добавлено поле `bookingStatus` в `InvoiceSerializer`
- `test_bug_011_calendar_status.py` - базовый тест (новый)
- `test_bug_011_calendar_status_full.py` - полный тест всех статусов (новый)
- `BUG_011_FIX.md` - документация (этот файл)
