# API Documentation - PIONEER Backend

## Базовый URL

```text
http://127.0.0.1:8000/api/
```

Все non-auth API в проекте сейчас работают как Bearer API. Глобальный middleware ожидает `Authorization: Bearer <access_token>` для запросов к `/api/*`, кроме путей под `/api/users/auth/`.

## Текущий статус API

- backend уже частично реализован и пригоден для dev/staging-интеграции;
- основной пользовательский auth flow для web-клиента: email-коды через `/api/users/auth/send-code/` и `/api/users/auth/verify-code/`;
- роли в коде: `ADMIN`, `ORGANIZATION`, `CLIENT`;
- публичная регистрация создаёт только `CLIENT`;
- рядом с основным auth flow в коде остаются legacy/specialized маршруты.

## Роли и доступ

| Роль | Что реально используется в коде |
| --- | --- |
| `ADMIN` | Полный доступ ко всем viewsets и user API |
| `ORGANIZATION` | Свои организации, свои услуги, бронирования по своим услугам |
| `CLIENT` | Чтение активных организаций и услуг, CRUD своих бронирований |

## Auth flow

### Основной flow для web-клиента

1. `POST /api/users/auth/send-code/`
2. `POST /api/users/auth/verify-code/`
3. сохранить `jwt.access`, `jwt.refresh` и `session.id`
4. использовать `Authorization: Bearer <access_token>`
5. при выходе вызвать `POST /api/users/auth/logout/` с `session_id`

Логика `send-code`/`verify-code`:

- пользователь не найден -> регистрация;
- пользователь найден и `name` заполнено -> обычный логин;
- пользователь найден, но `name` пустое -> завершение регистрации.

### Auth endpoints: primary vs legacy/specialized

#### Основные

- `POST /api/users/auth/send-code/`
- `POST /api/users/auth/verify-code/`

#### Legacy / specialized

- `POST /api/users/auth/email/register/send-code/`
- `POST /api/users/auth/email/register/verify-code/`
- `POST /api/users/auth/email/login/send-code/`
- `POST /api/users/auth/email/login/verify-code/`
- `POST /api/users/auth/recovery/send-code/`
- `POST /api/users/auth/recovery/verify-code/`
- `POST /api/users/auth/logout/`
- `POST /api/users/auth/jwt/verify/`

`/api/users/auth/email/register/*` и `/api/users/auth/email/login/*` сохраняются как совместимый/старый surface. Для нового web-клиента ориентируйтесь на universal flow.

## Аутентификация

### 1. Отправить код - основной endpoint

```http
POST /api/users/auth/send-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "privacy_policy_accepted": true
}
```

Поля:

- `email` — обязателен всегда;
- `privacy_policy_accepted` — обязателен только если flow оказывается регистрацией или завершением регистрации.

Ответ:

```json
{
  "message": "Код для регистрации отправлен на email",
  "email": "user@example.com",
  "auth_type": "registration",
  "dev_code": "4444"
}
```

`auth_type` может быть:

- `registration`
- `login`
- `complete_registration`

Типичные ошибки:

- `400` — пустой email;
- `400` — некорректный email;
- `400` — не принят privacy policy для регистрации / завершения регистрации;
- `500` — send-code провалился на уровне сервиса отправки.

Важно:

- в `DEBUG=True` ответ может содержать `dev_code`;
- verify flow также принимает код `4444`;
- send endpoint не раскрывает детали resend cooldown наружу, даже если сервис отправки их учитывает.

### 2. Проверить код - основной endpoint

```http
POST /api/users/auth/verify-code/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "4444",
  "device_id": "web-chrome-01",
  "name": "Иван Иванов",
  "privacy_policy_accepted": true
}
```

Поля:

- `email`, `code`, `device_id` — обязательны всегда;
- `name` и `privacy_policy_accepted` — обязательны для регистрации и завершения регистрации;
- для обычного логина `name` не нужен.

Ответ:

```json
{
  "message": "Регистрация успешна",
  "user": {
    "id": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
    "email": "user@example.com",
    "name": "Иван Иванов",
    "role": "CLIENT",
    "is_new": true
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

Типичные ошибки:

- `400` — отсутствует одно из обязательных полей `email`, `code`, `device_id`;
- `400` — код не найден или истёк;
- `400` — неверный код, ответ содержит `attempts_left`;
- `400` — не передан `name` для регистрации / завершения регистрации;
- `400` — не принят privacy policy.

### 3. Legacy registration

```http
POST /api/users/auth/email/register/send-code/
POST /api/users/auth/email/register/verify-code/
```

Особенности текущего legacy flow:

- создаёт нового `CLIENT`;
- `verify` не принимает `name`;
- в результате пользователь может быть создан с `name = null`.

Именно поэтому для нового web-клиента основным считается universal auth flow.

### 4. Legacy login

```http
POST /api/users/auth/email/login/send-code/
POST /api/users/auth/email/login/verify-code/
```

Используйте только если вам нужен старый раздельный flow. Поведение по JWT и `UserSession` такое же, как у универсальных endpoints.

### 5. Recovery

```http
POST /api/users/auth/recovery/send-code/
POST /api/users/auth/recovery/verify-code/
```

Пример отправки кода:

```http
POST /api/users/auth/recovery/send-code/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Особенности:

- `send-code` всегда возвращает `200`, даже если пользователя с таким email нет;
- recovery verify после успешного кода тоже создаёт `UserSession` и выдаёт JWT.

### 6. Logout

```http
POST /api/users/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "session_id": "de3ad2ad-d5d6-48c0-8f55-8ff0ad88cd2f"
}
```

Ответ:

```json
{
  "message": "Выход выполнен"
}
```

`session_id` нужно брать из auth-ответа. Logout деактивирует соответствующий `UserSession`.

### 7. Проверка JWT

```http
POST /api/users/auth/jwt/verify/
Content-Type: application/json

{
  "token": "eyJ..."
}
```

Ответ:

```json
{
  "valid": true,
  "user": {
    "id": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
    "email": "user@example.com",
    "name": "Иван Иванов",
    "role": "CLIENT",
    "roles": ["CLIENT"],
    "is_active": true
  },
  "token": {
    "user_id": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
    "exp": 1775815200,
    "iat": 1775813400
  }
}
```

### 8. Refresh token

JWT refresh token выдаётся в auth-ответах, но публичный endpoint вроде `/api/token/refresh/` в проекте сейчас не подключён. Не закладывайтесь на него как на доступный API-маршрут.

## Users API

### `/api/users/me/`

```http
GET /api/users/me/
Authorization: Bearer <access_token>
```

Ответ:

```json
{
  "id": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "email": "user@example.com",
  "name": "Иван Иванов",
  "role": "CLIENT",
  "is_active": true,
  "privacy_policy_accepted_at": "2026-03-11T09:00:00Z",
  "created_at": "2026-03-11T09:00:00Z",
  "last_login_at": "2026-03-11T09:05:00Z"
}
```

### `/api/users/` и `/api/users/{id}/`

Роутер регистрирует стандартный DRF `ModelViewSet` только для `ADMIN`.

Практически это означает:

- `GET /api/users/`
- `POST /api/users/`
- `GET /api/users/{id}/`
- `PUT /api/users/{id}/`
- `PATCH /api/users/{id}/`
- `DELETE /api/users/{id}/`

Но важно понимать:

- публичный onboarding идёт через auth endpoints, а не через admin user CRUD;
- отдельного create/update контракта для admin user API в проекте пока не выделено.

## Cities API

### Список городов

```http
GET /api/organizations/cities/
Authorization: Bearer <access_token>
```

Доступ: любой аутентифицированный пользователь.

Поддерживаются:

- поиск: `?search=самара`
- сортировка: `?ordering=name`

Ответ:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Самара",
      "region": "Самарская область",
      "country": "Россия",
      "is_active": true,
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

Роутер также даёт `GET /api/organizations/cities/{id}/`.

## Organizations API

### Доступ и видимость

- `ADMIN` видит все организации;
- `ORGANIZATION` видит только свои организации;
- `CLIENT` видит только активные организации и только read-only.

### Список организаций

```http
GET /api/organizations/?city=1&is_active=true&search=мойка&ordering=-created_at
Authorization: Bearer <access_token>
```

Фильтры:

- `city`
- `is_active`

Поиск:

- `name`
- `description`

Сортировка:

- `name`
- `created_at`

### Создать организацию

```http
POST /api/organizations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Чистый Кузов",
  "city": 1,
  "address": "ул. Московское шоссе, 100",
  "phone": "+7 846 200-10-01",
  "email": "org@example.com",
  "description": "Мойка и детейлинг",
  "is_active": true
}
```

Важно:

- `perform_create()` принудительно проставляет `owner = request.user`;
- `city`, `address`, `phone`, `email`, `description` в текущей модели необязательны;
- при создании через API нельзя надёжно назначить произвольного owner, даже если поле есть в serializer.

Ответ:

```json
{
  "id": 5,
  "name": "Чистый Кузов",
  "owner": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "owner_email": "org-owner@example.com",
  "city": 1,
  "city_name": "Самара",
  "address": "ул. Московское шоссе, 100",
  "phone": "+7 846 200-10-01",
  "email": "org@example.com",
  "description": "Мойка и детейлинг",
  "is_active": true,
  "created_at": "2026-03-11T09:15:00Z"
}
```

Роутер также даёт:

- `GET /api/organizations/{id}/`
- `PUT /api/organizations/{id}/`
- `PATCH /api/organizations/{id}/`
- `DELETE /api/organizations/{id}/`

## Services API

### Services

Доступ:

- `ADMIN` — все услуги;
- `ORGANIZATION` — услуги своих организаций;
- `CLIENT` — только активные услуги и только чтение.

Список / фильтры:

```http
GET /api/services/?organization=1&is_active=true&search=мойка&ordering=price
Authorization: Bearer <access_token>
```

Фильтры:

- `organization`
- `is_active`

Поиск:

- `title`
- `description`

Сортировка:

- `price`
- `created_at`

Создание:

```http
POST /api/services/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "organization": 1,
  "title": "Мойка",
  "description": "Ручная мойка автомобиля",
  "price": "500.00",
  "duration": 60,
  "is_active": true
}
```

Особенности:

- для `ADMIN` доступно создание услуги для любой организации;
- для `ORGANIZATION` обязательна передача `organization`, и она должна принадлежать текущему пользователю;
- в read-ответах `Service` уже содержит вложенные `items`.

Пример ответа:

```json
{
  "id": 10,
  "organization": 1,
  "organization_name": "Чистый Кузов",
  "title": "Мойка",
  "description": "Ручная мойка автомобиля",
  "price": "500.00",
  "duration": 60,
  "is_active": true,
  "items": [
    {
      "id": 15,
      "service": 10,
      "name": "Мойка кузова",
      "description": "",
      "price": "350.00",
      "is_required": false,
      "is_active": true,
      "order": 0,
      "created_at": "2026-03-11T09:20:00Z"
    }
  ],
  "created_at": "2026-03-11T09:18:00Z"
}
```

### Service items

Роуты:

- `GET /api/services/items/`
- `POST /api/services/items/`
- `GET /api/services/items/{id}/`
- `PUT /api/services/items/{id}/`
- `PATCH /api/services/items/{id}/`
- `DELETE /api/services/items/{id}/`

Фильтры:

- `service`
- `is_required`
- `is_active`

Сортировка:

- `order`
- `name`

Видимость списка:

- `ADMIN` — все элементы;
- `ORGANIZATION` — элементы услуг своих организаций;
- `CLIENT` — только активные элементы активных услуг.

Важно:

- write-права для `ServiceItemViewSet` пока не усилены отдельной role-based permission;
- фактически write endpoints доступны любому аутентифицированному пользователю, если он знает корректный payload;
- это текущий gap реализации, а не желаемое продуктовое поведение.

Пример payload:

```http
POST /api/services/items/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service": 10,
  "name": "Пылесос салона",
  "description": "",
  "price": "250.00",
  "is_required": false,
  "is_active": true,
  "order": 1
}
```

## Bookings API

### Доступ

- `ADMIN` — все бронирования;
- `ORGANIZATION` — бронирования по услугам своих организаций;
- `CLIENT` — только свои бронирования.

### Список бронирований

```http
GET /api/bookings/?status=NEW&service=10&ordering=-scheduled_at
Authorization: Bearer <access_token>
```

Фильтры:

- `status`
- `service`

Поиск:

- `user__phone`
- `service__title`

Сортировка:

- `scheduled_at`
- `created_at`

### Создать бронирование

```http
POST /api/bookings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service": 10,
  "scheduled_at": "2026-03-20T10:00:00Z",
  "status": "NEW"
}
```

Особенности текущей реализации:

- `perform_create()` всегда подставляет `user = request.user`;
- `status` можно передать сразу, если он соответствует choices модели;
- API пока не создаёт `BookingItem` через booking payload;
- нет проверки слотов, конфликтов времени и строгих переходов статусов.

Пример ответа:

```json
{
  "id": 42,
  "user": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "user_email": "client@example.com",
  "service": 10,
  "service_title": "Мойка",
  "status": "NEW",
  "scheduled_at": "2026-03-20T10:00:00Z",
  "items": [],
  "created_at": "2026-03-11T09:30:00Z",
  "updated_at": "2026-03-11T09:30:00Z"
}
```

Роутер также даёт:

- `GET /api/bookings/{id}/`
- `PUT /api/bookings/{id}/`
- `PATCH /api/bookings/{id}/`
- `DELETE /api/bookings/{id}/`

С точки зрения текущего кода это базовый CRUD, а не завершённый booking workflow.

## Пагинация

Все list endpoints используют `PageNumberPagination`.

По умолчанию:

- размер страницы: `20`

Формат:

```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/services/?page=3",
  "previous": "http://127.0.0.1:8000/api/services/?page=1",
  "results": []
}
```

## Формат ошибок

### 401

```json
{
  "error": "Требуется авторизация",
  "detail": "Вы не авторизованы. Пожалуйста, войдите в систему.",
  "code": "not_authenticated"
}
```

### 403

```json
{
  "error": "Доступ запрещен",
  "detail": "У вас нет прав для выполнения этого действия.",
  "code": "permission_denied"
}
```

## Что ещё не стабилизировано

- нет публичного refresh endpoint;
- основная бизнес-логика бронирований пока ограничена CRUD;
- `BookingItem` не создаётся через booking API;
- права записи для `ServiceItem` нужно ужесточить;
- тесты для `organizations`, `services` и `bookings` пока почти отсутствуют;
- конфигурация `settings.py`, Dockerfile и Compose-файл ориентированы на разработку, а не на production.

## Связанные документы

- [README.md](README.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [DOCKER_SETUP.md](DOCKER_SETUP.md)
