# API Documentation - Pioneer Backend

## Базовый URL
```
http://127.0.0.1:8000/api/
```

## Аутентификация

Система использует беспарольную аутентификацию через email-коды.

### Особенности:
- ✅ Регистрация и вход через email-код (БЕЗ ПАРОЛЕЙ)
- ✅ JWT токены (access + refresh)
- ✅ Одна активная сессия на одном устройстве
- ✅ TTL email-кода: 5 минут
- ✅ Максимум 5 попыток ввода кода
- ✅ Тестовый код в dev режиме: 4444

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
- Просмотр активных организаций (только чтение)
- Просмотр активных услуг (только чтение)
- Создание и управление своими бронированиями

---

## Endpoints

### Аутентификация

Система использует беспарольную аутентификацию через email-коды с **универсальными эндпоинтами**, которые автоматически определяют тип операции (регистрация или вход) по наличию имени пользователя в базе данных.

### Особенности:
- ✅ **Универсальные эндпоинты** - один URL для регистрации и входа
- ✅ Автоматическое определение типа операции по полю `name` в БД
- ✅ Беспарольная аутентификация через email-коды
- ✅ JWT токены (access + refresh)
- ✅ Одна активная сессия на одном устройстве
- ✅ TTL email-кода: 5 минут
- ✅ Максимум 5 попыток ввода кода
- ✅ Тестовый код в dev режиме: 4444

### Логика универсальных эндпоинтов:
- **Пользователь не существует** → регистрация (требует `name` и `privacy_policy_accepted`)
- **Пользователь существует, `name` заполнено** → обычный вход
- **Пользователь существует, `name` пустое** → завершение регистрации (требует `name` и `privacy_policy_accepted`)

---

#### 1. Отправить код (универсальный) - ОСНОВНОЙ ЭНДПОИНТ

```http
POST /api/users/auth/send-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "privacy_policy_accepted": true  // обязательно для регистрации/завершения регистрации
}
```

**Ответ (200 OK):**
```json
{
  "message": "Код для входа отправлен на email",
  "email": "user@example.com",
  "auth_type": "login",  // "registration", "login", "complete_registration"
  "dev_code": "4444"
}
```

**Ошибки:**
- `400` - Email обязателен
- `400` - Некорректный email
- `400` - Необходимо принять политику конфиденциальности (для регистрации/завершения регистрации)

---

#### 2. Проверить код (универсальный) - ОСНОВНОЙ ЭНДПОИНТ

```http
POST /api/users/auth/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier",
  "name": "Имя пользователя",  // обязательно для регистрации/завершения регистрации
  "privacy_policy_accepted": true  // обязательно для регистрации/завершения регистрации
}
```

**Ответ (200 OK):**
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Имя пользователя",
    "role": "CLIENT",
    "is_new": false
  },
  "session": {
    "id": "uuid",
    "expires_at": "2026-04-09T12:00:00Z"
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Ошибки:**
- `400` - Необходимы: email, code, device_id
- `400` - Код не найден или истёк. Запросите новый код.
- `400` - Превышено количество попыток. Запросите новый код.
- `400` - Неверный код (+ attempts_left)
- `400` - Необходимо указать имя для регистрации/завершения регистрации
- `400` - Необходимо принять политику конфиденциальности

---

#### Дополнительные эндпоинты

Эти эндпоинты доступны для специфичных случаев, но рекомендуется использовать универсальные эндпоинты выше.

#### 3. Восстановление доступа

```http
POST /api/users/auth/recovery/send-code/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Код восстановления отправлен на email",
  "email": "user@example.com",
  "dev_code": "4444"
}
```

---

#### 4. Проверить код восстановления

```http
POST /api/users/auth/recovery/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Восстановление доступа успешно",
  "user": {...},
  "session": {...},
  "jwt": {...}
}
```

---

#### 5. Выйти из системы

```http
POST /api/users/auth/logout/
Content-Type: application/json
Authorization: Bearer <access_token>

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

#### 6. Обновить access токен

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Ответ (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---
}
```

**Ответ (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "phone": "79001234567",
    "role": "CLIENT",
    "is_active": true,
    "created_at": "2026-02-18T12:00:00Z"
  }
}
```

**Ошибки:**
- `400` - Необходимы: email, code, device_id
- `400` - Код не найден или истёк. Запросите новый код.
- `400` - Превышено количество попыток. Запросите новый код.
- `400` - Неверный код (+ attempts_left)

---

#### 5. Отправить email-код для входа (существующий пользователь)

```http
POST /api/users/auth/email/login/send-code/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Код восстановления отправлен на email",
  "email": "user@example.com",
  "dev_code": "4444"  // ТОЛЬКО ДЛЯ РАЗРАБОТКИ!
}
```

---

#### 6. Проверить email-код входа

```http
POST /api/users/auth/email/login/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Авторизация успешна",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Имя пользователя",
    "role": "CLIENT",
    "is_new": false
  },
  "session": {
    "id": "uuid",
    "expires_at": "2026-03-10T12:00:00Z"
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

#### 7. Отправить код для восстановления доступа

```http
POST /api/users/auth/email/recovery/send-code/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Код восстановления отправлен на email",
  "email": "user@example.com",
  "dev_code": "4444"
}
```

---

#### 8. Проверить код восстановления

```http
POST /api/users/auth/email/recovery/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "unique-device-identifier"
}
```

**Ответ (200 OK):**
```json
{
  "message": "Восстановление доступа успешно",
  "user": {...},
  "session": {...},
  "jwt": {...}
}
```

---

#### 9. Выйти из системы

```http
POST /api/users/auth/email/logout/
Content-Type: application/json
Authorization: Bearer <access_token>

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

#### 10. Обновить access токен

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Ответ (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Users (Пользователи)

#### Получить профиль текущего пользователя
```http
GET /api/users/me/
Authorization: Bearer <access_token>
```

**Ответ:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "phone": "79001234567",
  "role": "CLIENT",
  "is_active": true,
  "privacy_policy_accepted_at": "2026-02-18T12:00:00Z",
  "created_at": "2026-02-18T12:00:00Z",
  "last_login_at": "2026-02-18T12:00:00Z"
}
```

---

#### Список пользователей (только ADMIN)
```http
GET /api/users/
Authorization: Bearer <access_token>
```

**Доступ:** Только ADMIN

---

#### Получить пользователя (только ADMIN)
```http
GET /api/users/{id}/
Authorization: Bearer <access_token>
```

**Доступ:** Только ADMIN

---

### Cities (Города)

#### Список городов
```http
GET /api/organizations/cities/
Authorization: Bearer <access_token>
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

**Доступ:** Все авторизованные пользователи

---

### Organizations (Организации)

#### Список организаций
```http
GET /api/organizations/
Authorization: Bearer <access_token>
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

---

#### Создать организацию
```http
POST /api/organizations/
Content-Type: application/json
Authorization: Bearer <access_token>

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

**Доступ:** ADMIN, ORGANIZATION

**Примечание:** `owner` устанавливается автоматически из текущего пользователя.

---

#### Получить организацию
```http
GET /api/organizations/{id}/
Authorization: Bearer <access_token>
```

**Доступ:** Все авторизованные пользователи

---

#### Обновить организацию
```http
PUT /api/organizations/{id}/
PATCH /api/organizations/{id}/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "name": "Новое название",
  "is_active": false
}
```

**Доступ:** 
- ADMIN: любую организацию
- ORGANIZATION: только свою организацию

---

#### Удалить организацию
```http
DELETE /api/organizations/{id}/
Authorization: Bearer <access_token>
```

**Доступ:** 
- ADMIN: любую организацию
- ORGANIZATION: только свою организацию

---

### Services (Услуги)

#### Список услуг
```http
GET /api/services/
Authorization: Bearer <access_token>
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

---

#### Создать услугу
```http
POST /api/services/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "organization": 1,
  "title": "Массаж спины",
  "description": "Расслабляющий массаж",
  "price": "2500.00",
  "duration": 60,
  "is_active": true
}
```

**Доступ:** 
- ADMIN: для любой организации
- ORGANIZATION: только для своей организации

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
Authorization: Bearer <access_token>
```

**Параметры:**
- `?service={id}` - фильтр по услуге
- `?is_required=true` - только обязательные элементы
- `?is_active=true` - только активные элементы
- `?ordering=order` - сортировка по порядку

**Доступ:**
- ADMIN: все элементы
- ORGANIZATION: элементы услуг своих организаций
- CLIENT: только активные элементы

---

#### Создать элемент услуги
```http
POST /api/services/items/
Content-Type: application/json
Authorization: Bearer <access_token>

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

**Доступ:** ADMIN, ORGANIZATION (только для услуг своих организаций)

---

### Bookings (Бронирования)

#### Список бронирований
```http
GET /api/bookings/
Authorization: Bearer <access_token>
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
- ORGANIZATION: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

---

#### Создать бронирование
```http
POST /api/bookings/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "service": 1,
  "scheduled_at": "2026-02-20T14:00:00Z",
  "status": "NEW"
}
```

**Доступ:** Все авторизованные пользователи

**Примечание:** `user` устанавливается автоматически из текущего пользователя.

**Ответ включает вложенные элементы:**
```json
{
  "id": 1,
  "user": "uuid",
  "user_email": "user@example.com",
  "service": 1,
  "service_title": "Массаж спины",
  "status": "NEW",
  "scheduled_at": "2026-02-20T14:00:00Z",
  "items": [],
  "created_at": "2026-02-18T12:00:00Z",
  "updated_at": "2026-02-18T12:00:00Z"
}
```

---

#### Получить бронирование
```http
GET /api/bookings/{id}/
Authorization: Bearer <access_token>
```

**Доступ:**
- ADMIN: любое бронирование
- ORGANIZATION: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

---

#### Обновить бронирование
```http
PUT /api/bookings/{id}/
PATCH /api/bookings/{id}/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "status": "CONFIRMED",
  "scheduled_at": "2026-02-20T15:00:00Z"
}
```

**Доступ:**
- ADMIN: любое бронирование
- ORGANIZATION: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

---

#### Удалить бронирование
```http
DELETE /api/bookings/{id}/
Authorization: Bearer <access_token>
```

**Доступ:**
- ADMIN: любое бронирование
- ORGANIZATION: бронирования на услуги своих организаций
- CLIENT: только свои бронирования

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
- `400` - Ошибка валидации
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден

### Формат ошибок

**401 (не авторизован):**
```json
{
  "error": "Требуется авторизация",
  "detail": "Вы не авторизованы. Пожалуйста, войдите в систему.",
  "code": "not_authenticated"
}
```

**403 (нет прав):**
```json
{
  "error": "Доступ запрещен",
  "detail": "Только администраторы имеют доступ к этому ресурсу",
  "code": "permission_denied"
}
```

---

## Примеры использования

### Сценарий 1: Универсальная авторизация/регистрация (Рекомендуется)

**1. Отправить код (система автоматически определит тип):**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "privacy_policy_accepted": true
  }'
```

**Ответ для нового пользователя:**
```json
{
  "message": "Код для регистрации отправлен на email",
  "email": "newuser@example.com", 
  "auth_type": "registration",
  "dev_code": "4444"
}
```

**2. Проверить код и завершить регистрацию:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "code": "4444",
    "device_id": "my-device-123",
    "name": "Иван Иванов",
    "privacy_policy_accepted": true
  }'
```

**Ответ:**
```json
{
  "message": "Регистрация успешна",
  "user": {
    "id": "uuid",
    "email": "newuser@example.com",
    "name": "Иван Иванов",
    "role": "CLIENT",
    "is_new": true
  },
  "session": {...},
  "jwt": {...}
}
```

**3. Повторный вход (тот же эндпоинт):**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com"
  }'
```

**Ответ для существующего пользователя:**
```json
{
  "message": "Код для входа отправлен на email",
  "email": "newuser@example.com",
  "auth_type": "login",
  "dev_code": "4444"
}
```

**4. Проверить код для входа:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "code": "4444",
    "device_id": "my-device-123"
  }'
```
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "privacy_policy_accepted": true
  }'
```

**Ответ для нового пользователя:**
```json
{
  "message": "Код для регистрации отправлен на email",
  "email": "newuser@example.com",
  "auth_type": "registration",
  "dev_code": "4444"
}
```

**2. Проверить код и завершить процесс:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "code": "4444",
    "device_id": "my-device-123",
    "name": "Иван Иванов",
    "privacy_policy_accepted": true
  }'
```

**3. Повторный вход (тот же эндпоинт):**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com"
  }'
```

**Ответ для существующего пользователя:**
```json
{
  "message": "Код для входа отправлен на email",
  "email": "newuser@example.com",
  "auth_type": "login",
  "dev_code": "4444"
}
```

---

### Сценарий 2: Регистрация клиента (отдельные эндпоинты)

**1. Отправить email-код для регистрации:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/email/register/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "privacy_policy_accepted": true
  }'
```

**2. Проверить код и авторизоваться:**
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/email/register/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "code": "4444",
    "device_id": "my-device-123",
    "privacy_policy_accepted": true
  }'
```

**Ответ:**
```json
{
  "message": "Регистрация успешна",
  "user": {
    "id": "uuid",
    "email": "client@example.com",
    "name": null,
    "role": "CLIENT",
    "is_new": true
  },
  "session": {
    "id": "uuid",
    "expires_at": "2026-04-09T12:00:00Z"
  },
  "jwt": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**3. Просмотр доступных услуг:**
```bash
curl -X GET http://127.0.0.1:8000/api/services/?is_active=true \
  -H "Authorization: Bearer <access_token>"
```

**4. Создание бронирования:**
```bash
curl -X POST http://127.0.0.1:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "service": 1,
    "scheduled_at": "2026-02-20T14:00:00Z"
  }'
```

---

### Сценарий 3: Владелец создает организацию и услугу

**1. Регистрация владельца:**
```bash
# Отправить код для регистрации
curl -X POST http://127.0.0.1:8000/api/users/auth/email/register/send-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@example.com",
    "privacy_policy_accepted": true
  }'

# Проверить код (роль ORGANIZATION устанавливается админом после регистрации)
curl -X POST http://127.0.0.1:8000/api/users/auth/email/register/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@example.com",
    "code": "4444",
    "device_id": "owner-device-123",
    "privacy_policy_accepted": true
  }'
```

**2. Создание организации:**
```bash
curl -X POST http://127.0.0.1:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
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
  -H "Authorization: Bearer <access_token>" \
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
  -H "Authorization: Bearer <access_token>"
```

---

## Безопасность

### Защита от брутфорса
- Максимум 5 попыток ввода email-кода
- После 5 неудачных попыток код становится недействительным
- Нужно запросить новый код

### Беспарольная система
- Пароли НЕ используются
- Вход только через email-коды
- Коды одноразовые и короткоживущие

### JWT токены
- Access token: 30 минут
- Refresh token: 30 дней
- Токены подписаны SECRET_KEY

### Одна активная сессия
- При логине на новом устройстве старая сессия деактивируется
- Хранится device_id и session_id

### TTL
- Email-код: 5 минут
- Access token: 30 минут
- Refresh token: 30 дней

### Проверка прав
- Все endpoints защищены (требуют авторизации)
- Проверка ролей на уровне ViewSet
- Object-level permissions для владения ресурсами
- Queryset filtering по ролям

---

## Email настройки

В режиме разработки:
- Код всегда: `4444`
- Email отправляется через Яндекс SMTP (Dmitry4424@yandex.ru)

**ВАЖНО:** Перед деплоем в продакшен:
1. Убрать тестовый код `4444`
2. Настроить production SMTP
3. Удалить поле `dev_code` из ответов API

---

## Дополнительная документация

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Схема базы данных
- [README.md](README.md) - Общая информация о проекте
