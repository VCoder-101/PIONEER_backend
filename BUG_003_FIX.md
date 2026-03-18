# БАГ-003: Исправление создания бронирования клиентом

**ID:** BUG-003 (TC-BOOK-01)  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

Пользователь с ролью CLIENT не мог создать бронирование. Система требовала поля `user` и `dateTime`, хотя:
- `user` должен устанавливаться автоматически из `request.user`
- `dateTime` - это алиас для `scheduled_at` (camelCase формат)

### Ошибка
```json
{
  "dateTime": ["This field is required."],
  "user": ["This field is required."]
}
```

## Решение

Обновлен `BookingSerializer` в `bookings/serializers.py`:

### Изменения

1. **Поле `user` помечено как read_only**
   ```python
   read_only_fields = ['id', 'user', 'created_at', 'updated_at']
   ```

2. **Поле `dateTime` настроено для записи**
   ```python
   dateTime = serializers.DateTimeField(
       source='scheduled_at', 
       format='%d/%m/%Y %H:%M', 
       required=False  # Добавлено
   )
   ```

3. **Поле `carModel` сделано опциональным**
   ```python
   carModel = serializers.CharField(source='car_model', required=False)
   ```

4. **Добавлен метод `validate()` для поддержки обоих форматов**
   - Поддерживает camelCase: `carModel`, `wheelDiameter`, `dateTime`
   - Поддерживает snake_case: `car_model`, `wheel_diameter`, `scheduled_at`

## Как работает

### Создание бронирования (camelCase формат)
```json
POST /api/bookings/
Authorization: Bearer <token>

{
  "service": 1,
  "scheduled_at": "2026-03-20T10:00:00Z",
  "status": "NEW",
  "carModel": "Lada Vesta",
  "wheelDiameter": 16
}
```

### Создание бронирования (snake_case формат)
```json
POST /api/bookings/
Authorization: Bearer <token>

{
  "service": 1,
  "scheduled_at": "2026-03-20T10:00:00Z",
  "status": "NEW",
  "car_model": "Lada Vesta",
  "wheel_diameter": 16
}
```

### Автоматические действия
- `user` устанавливается из `request.user` в `BookingViewSet.perform_create()`
- `status` по умолчанию `NEW` (если не указан)
- `created_at` и `updated_at` устанавливаются автоматически

## Тестирование

### Автоматический тест
```bash
python test_bug_003_booking_create.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-003 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Авторизация под клиентом
2. ✅ Создание бронирования с camelCase полями
3. ✅ Поле `user` устанавливается автоматически
4. ✅ Бронирование создается со статусом 201

## Измененные файлы

- `bookings/serializers.py` - обновлен `BookingSerializer`

## Чеклист

- [x] Обновлен `bookings/serializers.py`
- [x] Создан тест `test_bug_003_booking_create.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API

## Ручное тестирование

### 1. Авторизация
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","privacy_policy_accepted":true}'

curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","code":"XXXX","device_id":"test","name":"Client","privacy_policy_accepted":true}'
```

### 2. Создание бронирования
```bash
curl -X POST http://127.0.0.1:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "service": 1,
    "scheduled_at": "2026-03-20T10:00:00Z",
    "status": "NEW",
    "carModel": "Lada Vesta",
    "wheelDiameter": 16
  }'
```

Ожидаемый ответ: **201 Created**
```json
{
  "id": 7,
  "service": 1,
  "status": "NEW",
  "user_email": "client@example.com",
  "car_model": "Lada Vesta",
  "wheel_diameter": 16,
  ...
}
```

## Связанные документы

- `bookings/models.py` - модель Booking
- `bookings/views.py` - BookingViewSet
- `bookings/permissions.py` - IsBookingOwnerOrServiceOwner
