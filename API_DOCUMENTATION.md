# API Documentation - Pioneer Backend

## Базовый URL
```
http://127.0.0.1:8000/api/
```

## Аутентификация
Используется Session Authentication. Для доступа к API необходимо войти через `/admin/` или использовать endpoint регистрации.

---

## Роли пользователей

### ADMIN
- Полный доступ ко всем ресурсам
- Управление пользователями
- Просмотр всех организаций, услуг и бронирований

### OWNER (Владелец организации)
- Создание и управление своими организациями
- Создание и управление услугами своих организаций
- Просмотр бронирований на услуги своих организаций

### CLIENT (Клиент)
- Просмотр всех организаций (только чтение)
- Просмотр активных услуг (только чтение)
- Создание и управление своими бронированиями

---

## Endpoints

### 1. Users (Пользователи)

#### Регистрация нового пользователя
```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "role": "CLIENT"  // ADMIN, OWNER, CLIENT
}
```

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "CLIENT",
  "is_active": true,
  "created_at": "2026-02-18T12:00:00Z"
}
```

#### Получить профиль текущего пользователя
```http
GET /api/users/me/
```

#### Список пользователей (только ADMIN)
```http
GET /api/users/
```

#### Получить пользователя (только ADMIN)
```http
GET /api/users/{id}/
```

---

### 2. Organizations (Организации)

#### Список организаций
```http
GET /api/organizations/
```

**Доступ:**
- ADMIN: все организации
- OWNER: только свои организации
- CLIENT: все организации (только чтение)

#### Создать организацию
```http
POST /api/organizations/
Content-Type: application/json

{
  "name": "Моя организация"
}
```

**Примечание:** `owner` устанавливается автоматически из текущего пользователя.

#### Получить организацию
```http
GET /api/organizations/{id}/
```

#### Обновить организацию
```http
PUT /api/organizations/{id}/
PATCH /api/organizations/{id}/
Content-Type: application/json

{
  "name": "Новое название"
}
```

#### Удалить организацию
```http
DELETE /api/organizations/{id}/
```

---

### 3. Services (Услуги)

#### Список услуг
```http
GET /api/services/
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
- OWNER: услуги своих организаций
- CLIENT: только активные услуги (только чтение)

#### Создать услугу
```http
POST /api/services/
Content-Type: application/json

{
  "organization": 1,
  "title": "Массаж спины",
  "description": "Расслабляющий массаж",
  "price": "2500.00",
  "duration": 60,
  "is_active": true
}
```

#### Получить услугу
```http
GET /api/services/{id}/
```

#### Обновить услугу
```http
PUT /api/services/{id}/
PATCH /api/services/{id}/
Content-Type: application/json

{
  "price": "3000.00",
  "is_active": false
}
```

#### Удалить услугу
```http
DELETE /api/services/{id}/
```

---

### 4. Bookings (Бронирования)

#### Список бронирований
```http
GET /api/bookings/
```

**Параметры фильтрации:**
- `?status=NEW` - фильтр по статусу (NEW, CONFIRMED, CANCELLED, DONE)
- `?service={id}` - фильтр по услуге
- `?search=user@example.com` - поиск по email пользователя или названию услуги
- `?ordering=scheduled_at` - сортировка по дате

**Примеры:**
```http
GET /api/bookings/?status=NEW
GET /api/bookings/?service=1&status=CONFIRMED
GET /api/bookings/?ordering=-scheduled_at
```

**Доступ:**
- ADMIN: все бронирования
- OWNER: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

#### Создать бронирование
```http
POST /api/bookings/
Content-Type: application/json

{
  "service": 1,
  "scheduled_at": "2026-02-20T14:00:00Z",
  "status": "NEW"
}
```

**Примечание:** `user` устанавливается автоматически из текущего пользователя.

#### Получить бронирование
```http
GET /api/bookings/{id}/
```

#### Обновить бронирование
```http
PUT /api/bookings/{id}/
PATCH /api/bookings/{id}/
Content-Type: application/json

{
  "status": "CONFIRMED",
  "scheduled_at": "2026-02-20T15:00:00Z"
}
```

#### Удалить бронирование
```http
DELETE /api/bookings/{id}/
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

---

## Примеры использования

### Сценарий 1: Регистрация клиента и создание бронирования

1. Регистрация:
```http
POST /api/users/register/
{
  "email": "client@example.com",
  "password": "password123",
  "role": "CLIENT"
}
```

2. Вход через админку: http://127.0.0.1:8000/admin/

3. Просмотр доступных услуг:
```http
GET /api/services/?is_active=true
```

4. Создание бронирования:
```http
POST /api/bookings/
{
  "service": 1,
  "scheduled_at": "2026-02-20T14:00:00Z"
}
```

### Сценарий 2: Владелец создает организацию и услугу

1. Регистрация владельца:
```http
POST /api/users/register/
{
  "email": "owner@example.com",
  "password": "password123",
  "role": "OWNER"
}
```

2. Создание организации:
```http
POST /api/organizations/
{
  "name": "Салон красоты"
}
```

3. Создание услуги:
```http
POST /api/services/
{
  "organization": 1,
  "title": "Стрижка",
  "description": "Мужская стрижка",
  "price": "1500.00",
  "duration": 30,
  "is_active": true
}
```

4. Просмотр бронирований на свои услуги:
```http
GET /api/bookings/
```
