# API Documentation - Pioneer Backend

## Базовый URL
```
http://127.0.0.1:8000/api/
```

## Аутентификация

Система использует аутентификацию по номеру телефона через SMS-код (без пароля).

### Особенности:
- ✅ Регистрация и вход через SMS-код
- ✅ Одна активная сессия на одном устройстве
- ✅ TTL SMS-кода: 5 минут
- ✅ Максимум 3 попытки ввода кода
- ✅ Защита от спама (1 минута между запросами)

---

## Роли пользователей

### ADMIN
- Полный доступ ко всем ресурсам
- Управление пользователями
- Просмотр всех организаций, услуг и бронирований

### ORGANIZATION (Владелец организации)
- Создание и управление своими организациями
- Создание и управление услугами своих организаций
- Просмотр бронирований на услуги своих организаций

### CLIENT (Клиент)
- Просмотр всех организаций (только чтение)
- Просмотр активных услуг (только чтение)
- Создание и управление своими бронированиями

---

## Endpoints

### Аутентификация

#### 1. Отправить SMS-код

```http
POST /api/users/auth/send-code/
Content-Type: application/json

{
  "phone": "8 (999) 123 45 67",
  "privacy_policy_accepted": true  // обязательно для новых пользователей
}
```

**Ответ (200 OK):**
```json
{
  "message": "SMS-код отправлен",
  "phone": "89991234567",
  "code_id": "uuid",
  "dev_code": "123456"  // ТОЛЬКО ДЛЯ РАЗРАБОТКИ!
}
```

**Ошибки:**
- `400` - Номер телефона обязателен
- `400` - Необходимо принять политику конфиденциальности
- `429` - Код уже отправлен. Подождите 1 минуту.

#### 2. Проверить SMS-код и авторизоваться

```http
POST /api/users/auth/verify-code/
Content-Type: application/json

{
  "phone": "8 (999) 123 45 67",
  "code": "123456",
  "device_id": "unique-device-identifier",
  "privacy_policy_accepted": true  // для новых пользователей
}
```

**Ответ (200 OK):**
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "uuid",
    "phone": "89991234567",
    "role": "CLIENT",
    "is_new": true
  },
  "session": {
    "id": "uuid",
    "expires_at": "2026-03-20T12:00:00Z"
  }
}
```

**Ошибки:**
- `400` - Необходимы: phone, code, device_id
- `400` - Код не найден или истёк. Запросите новый код.
- `400` - Превышено количество попыток. Запросите новый код.
- `400` - Неверный код (+ attempts_left)

#### 3. Выйти из системы

```http
POST /api/users/auth/logout/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "session_id": "uuid"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Выход выполнен"
}
```

---

### Users (Пользователи)

#### Получить профиль текущего пользователя
```http
GET /api/users/me/
Authorization: Bearer <session_id>
```

**Ответ:**
```json
{
  "id": "uuid",
  "phone": "89991234567",
  "role": "CLIENT",
  "is_active": true,
  "privacy_policy_accepted_at": "2026-02-18T12:00:00Z",
  "created_at": "2026-02-18T12:00:00Z",
  "last_login_at": "2026-02-18T12:00:00Z"
}
```

#### Список пользователей (только ADMIN)
```http
GET /api/users/
Authorization: Bearer <session_id>
```

#### Получить пользователя (только ADMIN)
```http
GET /api/users/{id}/
Authorization: Bearer <session_id>
```

---

### Cities (Города)

#### Список городов
```http
GET /api/organizations/cities/
Authorization: Bearer <session_id>
```

**Параметры:**
- `?search=Москва` - поиск по названию или региону

**Ответ:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Москва",
      "region": "Московская область",
      "country": "Россия",
      "is_active": true,
      "created_at": "2026-02-18T12:00:00Z"
    }
  ]
}
```

---

### Organizations (Организации)

#### Список организаций
```http
GET /api/organizations/
Authorization: Bearer <session_id>
```

**Параметры фильтрации:**
- `?city={id}` - фильтр по городу
- `?is_active=true` - только активные организации
- `?search=салон` - поиск по названию и описанию
- `?ordering=name` - сортировка по названию

**Примеры:**
```http
GET /api/organizations/?city=1
GET /api/organizations/?is_active=true&search=салон
GET /api/organizations/?ordering=-created_at
```

**Доступ:**
- ADMIN: все организации
- ORGANIZATION: только свои организации
- CLIENT: только активные организации (только чтение)

#### Создать организацию
```http
POST /api/organizations/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "name": "Салон красоты",
  "city": 1,
  "address": "ул. Ленина, 1",
  "phone": "+7 (999) 123-45-67",
  "email": "salon@example.com",
  "description": "Лучший салон в городе",
  "is_active": true
}
```

**Примечание:** `owner` устанавливается автоматически из текущего пользователя.

#### Получить организацию
```http
GET /api/organizations/{id}/
Authorization: Bearer <session_id>
```

#### Обновить организацию
```http
PUT /api/organizations/{id}/
PATCH /api/organizations/{id}/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "name": "Новое название",
  "is_active": false
}
```

#### Удалить организацию
```http
DELETE /api/organizations/{id}/
Authorization: Bearer <session_id>
```

---

### Services (Услуги)

#### Список услуг
```http
GET /api/services/
Authorization: Bearer <session_id>
```

**Параметры фильтрации:**
- `?organization={id}` - фильтр по организации
- `?is_active=true` - только активные услуги
- `?search=массаж` - поиск по названию и описанию
- `?ordering=price` - сортировка по цене (добавить `-` для обратного порядка)

**Примеры:**
```http
GET /api/services/?organization=1
GET /api/services/?is_active=true&search=массаж
GET /api/services/?ordering=-price
```

**Доступ:**
- ADMIN: все услуги
- ORGANIZATION: услуги своих организаций
- CLIENT: только активные услуги (только чтение)

#### Создать услугу
```http
POST /api/services/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "organization": 1,
  "title": "Массаж спины",
  "description": "Расслабляющий массаж",
  "price": "2500.00",
  "duration": 60,
  "is_active": true
}
```

**Ответ включает вложенные элементы услуги:**
```json
{
  "id": 1,
  "organization": 1,
  "organization_name": "Салон красоты",
  "title": "Массаж спины",
  "description": "Расслабляющий массаж",
  "price": "2500.00",
  "duration": 60,
  "is_active": true,
  "items": [],
  "created_at": "2026-02-18T12:00:00Z"
}
```

---

### Service Items (Элементы услуг)

#### Список элементов услуг
```http
GET /api/services/items/
Authorization: Bearer <session_id>
```

**Параметры:**
- `?service={id}` - фильтр по услуге
- `?is_required=true` - только обязательные элементы
- `?is_active=true` - только активные элементы
- `?ordering=order` - сортировка по порядку

#### Создать элемент услуги
```http
POST /api/services/items/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "service": 1,
  "name": "Ароматические масла",
  "description": "Дополнительные масла для массажа",
  "price": "500.00",
  "is_required": false,
  "is_active": true,
  "order": 1
}
```

---

### Bookings (Бронирования)

#### Список бронирований
```http
GET /api/bookings/
Authorization: Bearer <session_id>
```

**Параметры фильтрации:**
- `?status=NEW` - фильтр по статусу (NEW, CONFIRMED, CANCELLED, DONE)
- `?service={id}` - фильтр по услуге
- `?search=89991234567` - поиск по телефону пользователя или названию услуги
- `?ordering=scheduled_at` - сортировка по дате

**Примеры:**
```http
GET /api/bookings/?status=NEW
GET /api/bookings/?service=1&status=CONFIRMED
GET /api/bookings/?ordering=-scheduled_at
```

**Доступ:**
- ADMIN: все бронирования
- ORGANIZATION: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

#### Создать бронирование
```http
POST /api/bookings/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "service": 1,
  "scheduled_at": "2026-02-20T14:00:00Z",
  "status": "NEW"
}
```

**Примечание:** `user` устанавливается автоматически из текущего пользователя.

**Ответ включает вложенные элементы:**
```json
{
  "id": 1,
  "user": "uuid",
  "user_phone": "89991234567",
  "service": 1,
  "service_title": "Массаж спины",
  "status": "NEW",
  "scheduled_at": "2026-02-20T14:00:00Z",
  "items": [],
  "created_at": "2026-02-18T12:00:00Z",
  "updated_at": "2026-02-18T12:00:00Z"
}
```

#### Получить бронирование
```http
GET /api/bookings/{id}/
Authorization: Bearer <session_id>
```

#### Обновить бронирование
```http
PUT /api/bookings/{id}/
PATCH /api/bookings/{id}/
Content-Type: application/json
Authorization: Bearer <session_id>

{
  "status": "CONFIRMED",
  "scheduled_at": "2026-02-20T15:00:00Z"
}
```

#### Удалить бронирование
```http
DELETE /api/bookings/{id}/
Authorization: Bearer <session_id>
```

---

## Статусы бронирований

- `NEW` - Новая (только создана)
- `CONFIRMED` - Подтверждена
- `CANCELLED` - Отменена
- `DONE` - Завершена

---

## Пагинация

Все списковые endpoints поддерживают пагинацию:

```http
GET /api/services/?page=2
```

**Ответ:**
```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/services/?page=3",
  "previous": "http://127.0.0.1:8000/api/services/?page=1",
  "results": [...]
}
```

По умолчанию: 20 элементов на страницу.

---

## Коды ответов

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс создан
- `204 No Content` - Ресурс удален
- `400 Bad Request` - Ошибка валидации
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `429 Too Many Requests` - Слишком много запросов

---

## Примеры использования

### Сценарий 1: Регистрация клиента и создание бронирования

**1. Отправить SMS-код:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 123 45 67",
    "privacy_policy_accepted": true
  }'
```

**2. Проверить код и авторизоваться:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 123 45 67",
    "code": "123456",
    "device_id": "my-device-123",
    "privacy_policy_accepted": true
  }'
```

**3. Просмотр доступных услуг:**
```bash
curl -X GET http://127.0.0.1:8000/api/services/?is_active=true \
  -H "Authorization: Bearer <session_id>"
```

**4. Создание бронирования:**
```bash
curl -X POST http://127.0.0.1:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{
    "service": 1,
    "scheduled_at": "2026-02-20T14:00:00Z"
  }'
```

### Сценарий 2: Владелец создает организацию и услугу

**1. Регистрация владельца:**
```bash
# Отправить код
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 888 77 66",
    "privacy_policy_accepted": true
  }'

# Проверить код (роль ORGANIZATION устанавливается админом)
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "8 (999) 888 77 66",
    "code": "123456",
    "device_id": "owner-device-123",
    "privacy_policy_accepted": true
  }'
```

**2. Создание организации:**
```bash
curl -X POST http://127.0.0.1:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{
    "name": "Салон красоты",
    "city": 1,
    "address": "ул. Ленина, 1",
    "phone": "+7 (999) 888-77-66"
  }'
```

**3. Создание услуги:**
```bash
curl -X POST http://127.0.0.1:8000/api/services/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{
    "organization": 1,
    "title": "Стрижка",
    "description": "Мужская стрижка",
    "price": "1500.00",
    "duration": 30,
    "is_active": true
  }'
```

**4. Просмотр бронирований на свои услуги:**
```bash
curl -X GET http://127.0.0.1:8000/api/bookings/ \
  -H "Authorization: Bearer <session_id>"
```

---

## Безопасность

### Защита от брутфорса
- Максимум 3 попытки ввода SMS-кода
- После 3 неудачных попыток код становится недействительным

### Защита от спама
- Минимум 1 минута между запросами кода на один номер

### Одна активная сессия
- При логине на новом устройстве старая сессия деактивируется

### TTL
- SMS-код: 5 минут
- Сессия: 30 дней

---

## Интеграция с SMS-провайдером

В режиме разработки код возвращается в ответе API.

**ВАЖНО:** Перед деплоем в продакшен:
1. Интегрировать SMS-провайдер (Twilio, SMS.ru, SMSC.ru)
2. Удалить поле `dev_code` из ответа `/api/users/auth/send-code/`
3. Настроить переменные окружения для SMS-провайдера

---

## Дополнительная документация

- [AUTH_SYSTEM.md](AUTH_SYSTEM.md) - Подробная документация системы аутентификации
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Схема базы данных
- [README.md](README.md) - Общая информация о проекте
