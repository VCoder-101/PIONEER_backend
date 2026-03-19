# Добавление поля phone в модель User

## Обзор

Добавлено обязательное поле `phone` в модель User для хранения номера телефона пользователя. Поле обязательно при регистрации и отображается в календаре записей организаций.

## Изменения

### 1. Модель User

**Файл:** `users/models.py`

Добавлено новое поле:

```python
phone = models.CharField(
    max_length=20,
    null=True,
    blank=True,
    verbose_name="Телефон",
    db_index=True,
    help_text="Номер телефона пользователя"
)
```

Характеристики:
- Максимальная длина: 20 символов
- Опционально (null=True, blank=True)
- Индексируется для быстрого поиска
- Формат свободный (можно использовать любой формат: +7, 8, с пробелами, дефисами и т.д.)

### 2. Сериализатор User

**Файл:** `users/serializers.py`

Добавлено поле `phone` в список полей:

```python
fields = ['id', 'email', 'name', 'phone', 'role', 'is_active', 'privacy_policy_accepted_at', 'created_at', 'last_login_at', 'cars']
```

### 3. Регистрация/Авторизация

**Файл:** `users/email_auth_views.py`

Обновлена функция `verify_universal_auth_code`:

#### При регистрации нового пользователя:
```python
# Проверка обязательности phone
if not phone:
    return Response(
        {"error": "Необходимо указать телефон для регистрации"},
        status=status.HTTP_400_BAD_REQUEST,
    )

user = User.objects.create_user(
    email=email, 
    name=name, 
    phone=phone,  # Обязательное поле
    role="CLIENT"
)
```

#### При завершении регистрации:
```python
# Проверка обязательности phone
if not phone:
    return Response(
        {"error": "Необходимо указать телефон для завершения регистрации"},
        status=status.HTTP_400_BAD_REQUEST,
    )

user.name = name
user.phone = phone
user.save(update_fields=['name', 'phone'])
```

### 4. Календарь бронирований

**Файл:** `bookings/serializers.py`

Добавлено поле `customerPhone` в `InvoiceSerializer`:

```python
class InvoiceSerializer(serializers.ModelSerializer):
    customerName = serializers.CharField(source='user.name', read_only=True)
    customerPhone = serializers.CharField(source='user.phone', read_only=True)
    # ... остальные поля
    
    class Meta:
        model = Booking
        fields = ['id', 'customerName', 'customerPhone', 'dateTime', 'carModel', 
                  'serviceMethod', 'duration', 'price', 'status', 'bookingStatus']
```

### 5. Миграция

**Файл:** `users/migrations/0007_user_phone.py`

Создана миграция для добавления поля `phone` в таблицу пользователей.

## API

### Регистрация с телефоном

```http
POST /api/users/auth/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "web-chrome-01",
  "name": "Иван Иванов",
  "phone": "+7 900 123-45-67",
  "privacy_policy_accepted": true
}
```

Поля:
- `phone` - обязательно при регистрации, номер телефона пользователя
- Если не указан при регистрации, вернется ошибка 400

Ответ:

```json
{
  "message": "Регистрация успешна",
  "user": {
    "id": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
    "email": "user@example.com",
    "name": "Иван Иванов",
    "phone": "+7 900 123-45-67",
    "role": "CLIENT",
    "is_new": true,
    "cars": []
  },
  "session": {
    "id": "de3ad2ad-d5d6-48c0-8f55-8ff0ad88cd2f",
    "expires_at": "2026-04-10T09:30:00+00:00"
  },
  "jwt": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

### Календарь бронирований

```http
GET /api/bookings/calendar/
Authorization: Bearer <access_token>
```

Ответ:

```json
{
  "count": 2,
  "results": [
    {
      "id": 10,
      "customerName": "Иван Петров",
      "customerPhone": "+7 900 123-45-67",
      "dateTime": "25/03/2026 10:00",
      "carModel": "BMW X5",
      "serviceMethod": "Комплексная мойка",
      "duration": "60",
      "price": "1000.00",
      "status": "NEW",
      "bookingStatus": "active"
    }
  ]
}
```

Поле `customerPhone`:
- Содержит номер телефона клиента
- Обязательное поле при регистрации
- Может быть `null` только для старых пользователей (зарегистрированных до добавления поля)
- Отображается в календаре для связи с клиентом

### Обновление профиля

Пользователь может обновить свой телефон через:

```http
PATCH /api/users/me/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "phone": "+7 900 123-45-67"
}
```

## Использование

### Для фронтенда

#### При регистрации:
```javascript
const response = await fetch('/api/users/auth/verify-code/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    code: '4444',
    device_id: 'web-chrome-01',
    name: 'Иван Иванов',
    phone: '+7 900 123-45-67',  // Обязательно
    privacy_policy_accepted: true
  })
});
```

#### В календаре организации:
```javascript
const response = await fetch('/api/bookings/calendar/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

const data = await response.json();
data.results.forEach(booking => {
  console.log(`Клиент: ${booking.customerName}`);
  console.log(`Телефон: ${booking.customerPhone || 'Не указан'}`);
  console.log(`Время: ${booking.dateTime}`);
});
```

## Валидация

Поле `phone` не имеет строгой валидации формата, что позволяет:
- Использовать любой формат номера телефона
- Указывать международные номера
- Использовать пробелы, дефисы, скобки для форматирования

Примеры допустимых форматов:
- `+7 900 123-45-67`
- `8 (900) 123-45-67`
- `+79001234567`
- `89001234567`
- `+1 (555) 123-4567`

## Обратная совместимость

⚠️ Breaking change для новых регистраций:
- Поле `phone` теперь обязательно при регистрации
- Существующие пользователи без телефона продолжают работать (поле может быть null)
- Новые пользователи должны указать телефон при регистрации
- API вернет ошибку 400 если phone не указан при регистрации

## Миграция данных

Для существующих пользователей:
- Поле `phone` может быть `null` (зарегистрированы до добавления обязательности)
- Пользователи могут добавить телефон через обновление профиля
- Новые пользователи обязаны указать телефон при регистрации

## Тестирование

### Тест 1: Регистрация с телефоном

```bash
# Отправить код
curl -X POST http://localhost:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","privacy_policy_accepted":true}'

# Подтвердить с телефоном
curl -X POST http://localhost:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "code":"XXXX",
    "device_id":"test",
    "name":"Test User",
    "phone":"+7 900 123-45-67",
    "privacy_policy_accepted":true
  }'
```

### Тест 2: Регистрация без телефона (должна быть ошибка)

```bash
curl -X POST http://localhost:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test2@example.com",
    "code":"XXXX",
    "device_id":"test",
    "name":"Test User 2",
    "privacy_policy_accepted":true
  }'

# Ожидаемый результат: 400 Bad Request
# {"error": "Необходимо указать телефон для регистрации"}
```

### Тест 3: Календарь с телефонами

```bash
curl http://localhost:8000/api/bookings/calendar/ \
  -H "Authorization: Bearer ${OWNER_TOKEN}"
```

## Файлы

### Измененные файлы
- `users/models.py` - добавлено поле phone
- `users/serializers.py` - добавлено поле в сериализатор
- `users/email_auth_views.py` - обработка phone при регистрации
- `bookings/serializers.py` - добавлено customerPhone в календарь
- `API_DOCUMENTATION.md` - обновлена документация

### Новые файлы
- `users/migrations/0007_user_phone.py` - миграция
- `PHONE_FIELD_IMPLEMENTATION.md` - этот файл

## Статус

✅ Реализовано и протестировано

Поле `phone` добавлено в модель User как обязательное при регистрации и отображается в календаре бронирований организаций.
