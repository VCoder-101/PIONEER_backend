# API Documentation - PIONEER Backend

## Последние обновления (Март 2026)

### Новая функциональность: Система управления расписанием и слотами

Реализована полноценная система управления временем работы организаций и доступными слотами для записи:

- **Расписание организаций** - настройка рабочих дней, времени работы, перерывов
- **Выходные дни** - управление праздниками и нерабочими днями
- **Доступность услуг** - специфичное расписание для отдельных услуг
- **Доступные слоты** - автоматическая генерация свободных слотов с учетом всех ограничений
- **Валидация бронирований** - автоматическая проверка доступности времени при создании записи

Подробности в разделе "Управление расписанием и доступными слотами" ниже.

### Исправленные баги

- **БАГ-001:** Инвалидация access токенов при обновлении - старые токены теперь немедленно инвалидируются
- **БАГ-002:** CLIENT теперь может создавать организации
- **БАГ-003:** Поле `user` в бронированиях устанавливается автоматически, поддержка camelCase
- **БАГ-004:** Rate limiting теперь возвращает 429 вместо 500
- **БАГ-005:** Поле `status` всегда возвращается в бронированиях
- **БАГ-006:** Добавлены поля `countServices` и `summaryPrice` в организации
- **БАГ-007:** Исправлена обработка URL без trailing slash
- **БАГ-008:** Владельцы организаций могут редактировать свои услуги
- **БАГ-009:** Добавлена проверка уникальности названия организации
- **БАГ-010:** Услуги можно создавать только для одобренных организаций
- **БАГ-011:** Календарь возвращает поле `bookingStatus` (active/archived)
- **БАГ-012:** Добавлена возможность управления видимостью организаций (is_active)

### Новые endpoints

- `POST /api/bookings/{id}/confirm/` - подтверждение бронирования (организация/админ)
- `POST /api/bookings/{id}/complete/` - завершение бронирования (организация/админ)
- `POST /api/organizations/{id}/toggle_active/` - переключить видимость организации (админ)
- `POST /api/organizations/{id}/activate/` - включить видимость организации (админ)
- `POST /api/organizations/{id}/deactivate/` - выключить видимость организации (админ)
- `GET/POST /api/organizations/schedules/` - управление расписанием организаций
- `GET/POST /api/organizations/holidays/` - управление выходными днями
- `GET/POST /api/organizations/service-availability/` - управление доступностью услуг
- `GET /api/organizations/available-slots/for_service/` - получение доступных слотов

### Breaking Changes

- **БАГ-001:** `/api/token/refresh/` теперь требует обязательное поле `device_id`

## Базовый URL

```text
http://127.0.0.1:8000/api/
```

Все non-auth API в проекте сейчас работают как Bearer API. Глобальный middleware ожидает `Authorization: Bearer <access_token>` для запросов к `/api/*`, кроме путей под `/api/users/auth/`.

## Текущий статус API

- backend уже частично реализован и пригоден для dev/staging-интеграции;
- основной пользовательский auth flow для web-клиента: email-коды через `/api/users/auth/send-code/` и `/api/users/auth/verify-code/`;
- роли в коде: `ADMIN`, `CLIENT` (роль `ORGANIZATION` удалена);
- публичная регистрация создаёт только `CLIENT`;
- владельцы организаций также имеют роль `CLIENT`, но связаны с организациями через поле `owner`;
- рядом с основным auth flow в коде остаются legacy/specialized маршруты.

## Роли и доступ

| Роль | Что реально используется в коде |
| --- | --- |
| `ADMIN` | Полный доступ ко всем viewsets и user API, управление заявками организаций |
| `CLIENT` | Чтение активных организаций и услуг, CRUD своих бронирований. Если владеет организациями - управление ими и их услугами |

**Важно:** Владельцы организаций определяются не по роли, а по связи `Organization.owner = User`. Они имеют роль `CLIENT`, но расширенные права на свои организации.

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
  "phone": "+7 900 123-45-67",
  "privacy_policy_accepted": true
}
```

Поля:

- `email`, `code`, `device_id` — обязательны всегда;
- `name`, `phone` и `privacy_policy_accepted` — обязательны для регистрации и завершения регистрации;
- для обычного логина `name` и `phone` не нужны.

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

**ВАЖНО:** После исправления БАГ-001, refresh token теперь инвалидирует старый access token.

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ...",
  "device_id": "unique-device-identifier"
}
```

**Обязательные поля:**
- `refresh` - refresh token из предыдущего ответа
- `device_id` - уникальный идентификатор устройства (ОБЯЗАТЕЛЬНО)

Ответ:

```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

Важно:
- Refresh endpoint НЕ требует Bearer токена в заголовке
- Отправляется refresh token и device_id в теле запроса
- Возвращается новый access token и новый refresh token
- **БАГ-001 FIX:** При обновлении токена старая сессия деактивируется
- **БАГ-001 FIX:** Старый access token становится невалидным немедленно
- **БАГ-001 FIX:** В JWT payload добавлен `session_id` для отслеживания активных сессий
- Refresh token остается действительным до истечения срока (30 дней)

**Breaking change:** Поле `device_id` теперь ОБЯЗАТЕЛЬНО. Обновите клиентский код.

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
  "last_login_at": "2026-03-11T09:05:00Z",
  "cars": [
    {
      "id": "bf76ba6e-367f-44d4-82dc-173b699c84f4",
      "brand": "Toyota",
      "license_plate": "A123BC77",
      "wheel_diameter": 16
    }
  ]
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

### Система заявок на подключение к агрегатору

Все организации проходят через систему заявок с тремя статусами:
- `pending` - на рассмотрении (по умолчанию при создании)
- `approved` - одобрена администратором
- `rejected` - отклонена администратором

### Доступ и видимость

- `ADMIN` видит все организации и может управлять заявками;
- Владельцы организаций (определяются по `Organization.owner`) видят только свои организации;
- `CLIENT` видит только одобренные активные организации и только read-only.

### Список организаций

```http
GET /api/organizations/?city=1&is_active=true&organization_status=approved&organization_type=wash&search=мойка&ordering=-created_at
Authorization: Bearer <access_token>
```

Фильтры:

- `city` - фильтр по городу
- `is_active` - активные/неактивные
- `organization_status` - статус заявки (pending/approved/rejected)
- `organization_type` - тип организации (wash/tire)

Поиск:

- `name` - название организации
- `description` - описание

Сортировка:

- `name` - по названию
- `created_at` - по дате создания

### Создать заявку на подключение организации

**БАГ-002 FIX:** Теперь CLIENT может создавать организации. Исправлена проверка прав.

**БАГ-009 FIX:** Добавлена проверка уникальности названия организации.

```http
POST /api/organizations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Чистый Кузов",
  "shortName": "ЧК",
  "organizationType": "wash",
  "city": 1,
  "address": "ул. Московское шоссе, 100",
  "phone": "+7 846 200-10-01",
  "email": "org@example.com",
  "description": "Мойка и детейлинг",
  "orgInn": "123456789012",
  "orgOgrn": "123456789012345",
  "orgKpp": "123456789",
  "wheelDiameters": [13, 14, 15, 16, 17, 18]
}
```

**Новые обязательные поля:**
- `shortName` - короткое название
- `organizationType` - тип организации ("wash" или "tire")
- `orgInn` - ИНН (до 12 символов)
- `orgOgrn` - ОГРН (до 15 символов)
- `orgKpp` - КПП (до 9 символов)
- `wheelDiameters` - массив диаметров дисков (для шиномонтажа)

Важно:

- `perform_create()` принудительно проставляет `owner = request.user`;
- `organization_status` автоматически устанавливается в "pending";
- `organizationStatus` и `owner` - read-only поля (БАГ-002);
- **БАГ-009:** Проверяется уникальность названия (case-insensitive);
- при создании через API нельзя надёжно назначить произвольного owner.

Ответ:

```json
{
  "id": 5,
  "name": "Чистый Кузов",
  "shortName": "ЧК",
  "organizationStatus": "pending",
  "organizationDateApproved": null,
  "owner": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "owner_email": "org-owner@example.com",
  "city": 1,
  "address": "ул. Московское шоссе, 100",
  "phone": "+7 846 200-10-01",
  "email": "org@example.com",
  "description": "Мойка и детейлинг",
  "is_active": true,
  "created_at": "2026-03-11T09:15:00Z",
  "organizationType": "wash",
  "orgOgrn": "123456789012345",
  "orgInn": "123456789012",
  "orgKpp": "123456789",
  "wheelDiameters": [13, 14, 15, 16, 17, 18],
  "countServices": 0,
  "summaryPrice": "0.00"
}
```

**БАГ-006 FIX:** Поля `countServices` и `summaryPrice` теперь возвращаются в ответе.

Возможные ошибки:
- `400` - Организация с таким названием уже существует (БАГ-009)

### Управление заявками (только для администраторов)

#### Получить заявки на рассмотрении

```http
GET /api/organizations/pending/
Authorization: Bearer <access_token>
```

Доступ: только `ADMIN`

Ответ:

```json
{
  "count": 2,
  "results": [
    {
      "id": 5,
      "name": "Чистый Кузов",
      "organizationStatus": "pending",
      "organizationDateApproved": null,
      ...
    }
  ]
}
```

#### Одобрить заявку

```http
POST /api/organizations/{id}/approve/
Authorization: Bearer <access_token>
```

Доступ: только `ADMIN`

Ответ:

```json
{
  "message": "Заявка одобрена",
  "organization": {
    "id": 5,
    "organizationStatus": "approved",
    "organizationDateApproved": "11/03/2026",
    ...
  }
}
```

#### Отклонить заявку

```http
POST /api/organizations/{id}/reject/
Authorization: Bearer <access_token>
```

Доступ: только `ADMIN`

Ответ:

```json
{
  "message": "Заявка отклонена",
  "organization": {
    "id": 5,
    "organizationStatus": "rejected",
    "organizationDateApproved": null,
    ...
  }
}
```

### Управление видимостью организаций (только для администраторов)

Администраторы могут управлять видимостью организаций через поле `is_active`. Это позволяет скрывать организации от клиентов без удаления.

#### Способ 1: Через PATCH запрос

```http
PATCH /api/organizations/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "is_active": false
}
```

Доступ: только `ADMIN`

Ответ:

```json
{
  "id": 5,
  "name": "Чистый Кузов",
  "is_active": false,
  ...
}
```

Важно:
- Только администраторы могут изменять `is_active`
- Владельцы организаций не могут изменять это поле
- При попытке изменения не-администратором вернется ошибка валидации

#### Способ 2: Специализированные endpoints

##### Переключить видимость

```http
POST /api/organizations/{id}/toggle_active/
Authorization: Bearer <access_token>
```

Изменяет `is_active` на противоположное значение.

Доступ: только `ADMIN`

Ответ:

```json
{
  "message": "Видимость организации выключена",
  "old_value": true,
  "new_value": false,
  "organization": {
    "id": 5,
    "is_active": false,
    ...
  }
}
```

##### Включить видимость

```http
POST /api/organizations/{id}/activate/
Authorization: Bearer <access_token>
```

Устанавливает `is_active = true`.

Доступ: только `ADMIN`

Ответ:

```json
{
  "message": "Видимость организации включена",
  "organization": {
    "id": 5,
    "is_active": true,
    ...
  }
}
```

##### Выключить видимость

```http
POST /api/organizations/{id}/deactivate/
Authorization: Bearer <access_token>
```

Устанавливает `is_active = false`.

Доступ: только `ADMIN`

Ответ:

```json
{
  "message": "Видимость организации выключена",
  "organization": {
    "id": 5,
    "is_active": false,
    ...
  }
}
```

#### Влияние is_active на видимость

- `is_active = true` - организация видна всем клиентам (если одобрена)
- `is_active = false` - организация скрыта от клиентов, но владелец и админ видят её

Клиенты видят только организации с `is_active=true` и `organization_status='approved'`.

Роутер также даёт:

- `GET /api/organizations/{id}/`
- `PUT /api/organizations/{id}/`
- `PATCH /api/organizations/{id}/`
- `DELETE /api/organizations/{id}/`

## Services API

### Services

**БАГ-010 FIX:** Пользователи могут создавать услуги только для одобренных организаций (status='approved').

Доступ:

- `ADMIN` — все услуги;
- Владельцы организаций — услуги своих одобренных организаций (БАГ-010);
- `CLIENT` — только активные услуги со статусом 'active' и только чтение.

### Система видимости услуг

Услуги имеют два уровня видимости:
- `is_active` - общая активность услуги
- `status` - статус видимости ('active' или 'ghost')

Клиенты видят только услуги с `is_active=true` и `status='active'`.
Владельцы организаций видят все свои услуги, включая скрытые ('ghost').

Список / фильтры:

```http
GET /api/services/?organization=1&is_active=true&status=active&search=мойка&ordering=price
Authorization: Bearer <access_token>
```

Фильтры:

- `organization` - фильтр по организации
- `is_active` - активные/неактивные
- `status` - статус видимости ('active'/'ghost')

Поиск:

- `title` - название услуги
- `description` - описание

Сортировка:

- `price` - по цене
- `created_at` - по дате создания

Создание:

**БАГ-010 FIX:** Создание услуги доступно только для одобренных организаций.

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
  "status": "active",
  "is_active": true
}
```

Важно:
- Пользователь должен быть владельцем организации
- Организация должна иметь статус 'approved' (БАГ-010)
- Если организация не одобрена, вернется 403 Forbidden

Возможные ошибки:
- `403` - Нет прав или организация не одобрена (БАГ-010)
- `400` - Некорректные данные

**Новые поля:**
- `status` - статус видимости ("active" или "ghost")

Особенности:

- для `ADMIN` доступно создание услуги для любой организации;
- для владельцев организаций обязательна передача `organization`, и она должна принадлежать текущему пользователю;
- владельцы могут редактировать свои услуги через `PUT/PATCH /api/services/{id}/`;
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
  "status": "active",
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
- Владельцы организаций — элементы услуг своих организаций;
- `CLIENT` — только активные элементы активных услуг со статусом 'active'.

Важно:

- write-права для `ServiceItemViewSet` контролируются через проверку владения организацией;
- владельцы организаций могут управлять элементами только своих услуг.

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

## Cars API

Гараж пользователя — список автомобилей, привязанных к аккаунту.

### Доступ

- `CLIENT` — видит и управляет только своими машинами.
- `ADMIN` — видит все машины в системе.

### Список машин

```http
GET /api/cars/
Authorization: Bearer <access_token>
```

Ответ:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "bf76ba6e-367f-44d4-82dc-173b699c84f4",
      "owner_email": "user@example.com",
      "brand": "Toyota",
      "license_plate": "A123BC77",
      "wheel_diameter": 16,
      "created_at": "2026-03-12T06:51:41.844816Z",
      "updated_at": "2026-03-12T06:51:41.844829Z"
    }
  ]
}
```

### Добавить машину

```http
POST /api/cars/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "brand": "Toyota",
  "license_plate": "A123BC77",
  "wheel_diameter": 16
}
```

Поля:

- `brand` — марка, строка (обязательно).
- `license_plate` — госномер, уникальный в системе (обязательно). Автоматически приводится к верхнему регистру.
- `wheel_diameter` — диаметр диска в дюймах, целое число от 10 до 30 (обязательно).

Ответ `201`:

```json
{
  "id": "bf76ba6e-367f-44d4-82dc-173b699c84f4",
  "owner_email": "user@example.com",
  "brand": "Toyota",
  "license_plate": "A123BC77",
  "wheel_diameter": 16,
  "created_at": "2026-03-12T06:51:41.844816Z",
  "updated_at": "2026-03-12T06:51:41.844829Z"
}
```

Типичные ошибки:

- `400` — госномер уже занят другим пользователем.
- `400` — `wheel_diameter` вне диапазона 10–30.

### Детали / редактировать / удалить

```http
GET    /api/cars/{id}/
PUT    /api/cars/{id}/
PATCH  /api/cars/{id}/
DELETE /api/cars/{id}/
Authorization: Bearer <access_token>
```

- `PUT/PATCH` принимает те же поля, что `POST`. Все поля необязательны для `PATCH`.
- `DELETE` возвращает `204 No Content`.
- Чужая машина возвращает `404`.

## Bookings API

### Доступ

- `ADMIN` — все бронирования;
- Владельцы организаций — бронирования по услугам своих организаций + свои собственные бронирования;
- `CLIENT` — только свои бронирования.

### Список бронирований

```http
GET /api/bookings/?status=NEW&service=10&ordering=-scheduled_at
Authorization: Bearer <access_token>
```

Фильтры:

- `status` - статус бронирования
- `service` - фильтр по услуге

Поиск:

- `user__email` - по email клиента
- `service__title` - по названию услуги

Сортировка:

- `scheduled_at` - по времени записи
- `created_at` - по дате создания

### Календарный формат (invoices)

```http
GET /api/bookings/calendar/
Authorization: Bearer <access_token>
```

**БАГ-011 FIX:** Теперь возвращает поле `bookingStatus` (active/archived).

Возвращает бронирования в упрощенном формате для календаря:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
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
    },
    {
      "id": 11,
      "customerName": "Мария Сидорова",
      "customerPhone": "+7 905 987-65-43",
      "dateTime": "25/03/2026 15:00",
      "carModel": "Toyota Camry",
      "serviceMethod": "Экспресс мойка",
      "duration": "30",
      "price": "500.00",
      "status": "CANCELLED",
      "bookingStatus": "archived"
    }
  ]
}
```

Поля в календарном формате:
- `customerName` - имя клиента
- `customerPhone` - телефон клиента (может быть null)
- `dateTime` - дата и время записи в формате DD/MM/YYYY HH:MM
- `carModel` - модель автомобиля
- `serviceMethod` - название услуги
- `duration` - длительность услуги в минутах
- `price` - стоимость услуги
- `status` - статус бронирования (NEW, CONFIRMED, CANCELLED, DONE)
- `bookingStatus` - статус для календаря (active/archived)

**БАГ-011 FIX:** Добавлено поле `bookingStatus`:
- `active` - NEW, CONFIRMED (активные бронирования)
- `archived` - CANCELLED, DONE (завершенные/отмененные)

**БАГ-005 FIX:** Поле `status` теперь всегда возвращается в ответе.

Поддерживает те же фильтры и сортировку, что и основной список.

### Создать бронирование

**БАГ-003 FIX:** Поле `user` устанавливается автоматически, поддержка camelCase и snake_case.

```http
POST /api/bookings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service": 10,
  "scheduled_at": "2026-03-20T10:00:00Z",
  "status": "NEW",
  "carModel": "Lada Vesta",
  "wheelDiameter": 16
}
```

**Новые поля:**
- `carModel` - модель автомобиля (опционально, БАГ-003)
- `wheelDiameter` - диаметр диска (опционально, БАГ-003)

**БАГ-003 FIX:** Важные изменения:
- Поле `user` НЕ требуется в запросе (устанавливается автоматически)
- Поля `dateTime` и `carModel` опциональны
- Поддерживается как camelCase (`dateTime`, `carModel`, `wheelDiameter`), так и snake_case (`scheduled_at`, `car_model`, `wheel_diameter`)

Особенности текущей реализации:

- `perform_create()` всегда подставляет `user = request.user`;
- `status` можно передать сразу, если он соответствует choices модели;
- API пока не создаёт `BookingItem` через booking payload;
- нет проверки слотов, конфликтов времени и строгих переходов статусов.

### Управление статусами бронирований

Есть два способа изменения статуса бронирования:

1. **Специализированные endpoints** (рекомендуется) - с валидацией переходов
2. **Стандартный PATCH** - прямое изменение статуса

#### Способ 1: Специализированные endpoints (рекомендуется)

##### Подтвердить бронирование

```http
POST /api/bookings/{id}/confirm/
Authorization: Bearer <access_token>
```

**Переход:** NEW → CONFIRMED

**Права доступа:**
- Владелец организации (для бронирований на свои услуги)
- Администратор

**Валидация:**
- Можно подтвердить только бронирования со статусом NEW
- Автоматическая проверка прав

Ответ:
```json
{
  "message": "Бронирование успешно подтверждено",
  "confirmed_by": "organization",
  "old_status": "NEW",
  "booking": { ... }
}
```

##### Завершить бронирование

```http
POST /api/bookings/{id}/complete/
Authorization: Bearer <access_token>
```

**Переход:** CONFIRMED → DONE

**Права доступа:**
- Владелец организации (для бронирований на свои услуги)
- Администратор

**Валидация:**
- Можно завершить только бронирования со статусом CONFIRMED
- Автоматическая проверка прав

Ответ:
```json
{
  "message": "Бронирование успешно завершено",
  "completed_by": "organization",
  "old_status": "CONFIRMED",
  "booking": { ... }
}
```

##### Отменить бронирование

```http
POST /api/bookings/{id}/cancel/
Authorization: Bearer <access_token>
```

Отменяет бронирование, устанавливая статус в `CANCELLED`.

**Права доступа:**
- Клиент может отменить своё бронирование
- Владелец организации может отменить любое бронирование на услуги своей организации
- Администратор может отменить любое бронирование

**Ограничения:**
- Нельзя отменить уже отмененное бронирование (статус `CANCELLED`)
- Нельзя отменить завершенное бронирование (статус `DONE`)

Ответ при успешной отмене:

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

Ошибки:

```json
// 403 - нет прав
{
  "error": "У вас нет прав на отмену этого бронирования"
}

// 400 - уже отменено
{
  "error": "Бронирование уже отменено"
}

// 400 - завершено
{
  "error": "Нельзя отменить завершенное бронирование"
}
```

#### Способ 2: Стандартный PATCH (альтернатива)

Можно также использовать стандартный PATCH endpoint для прямого изменения статуса:

```http
PATCH /api/bookings/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "CONFIRMED"
}
```

**Доступные статусы:**
- `NEW` - новое бронирование
- `CONFIRMED` - подтвержденное
- `CANCELLED` - отмененное
- `DONE` - завершенное

**Важно:**
- PATCH не выполняет валидацию переходов статусов
- PATCH не проверяет бизнес-логику (например, можно изменить DONE на NEW)
- Рекомендуется использовать специализированные endpoints для корректной работы

**Пример:**
```javascript
// Подтверждение через PATCH
fetch(`http://localhost:8000/api/bookings/${invoiceId}/`, {
  method: 'PATCH',
  headers: {
    "Authorization": `Bearer ${access_token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({"status": "CONFIRMED"})
})
```

### Формат ответа

API поддерживает два формата ответа:

#### Полный формат (стандартный DRF)

```json
{
  "id": 42,
  "user": "cfa2a7cf-35c4-40c5-b50c-cc4cfcb2c8f7",
  "user_email": "client@example.com",
  "service": 10,
  "service_title": "Мойка",
  "status": "NEW",
  "scheduled_at": "2026-03-20T10:00:00Z",
  "car_model": "Lada Vesta",
  "wheel_diameter": 16,
  "items": [],
  "created_at": "2026-03-11T09:30:00Z",
  "updated_at": "2026-03-11T09:30:00Z"
}
```

#### Формат invoices (для фронтенда)

Каждое бронирование также содержит поля в формате invoices:

```json
{
  "id": 42,
  "customerName": "Иван Петров",
  "dateTime": "20/03/2026 10:00",
  "carModel": "Lada Vesta",
  "serviceMethod": "Мойка",
  "duration": "60",
  "price": "500.00",
  "wheelDiameter": 16,
  ...
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

- основная бизнес-логика бронирований пока ограничена CRUD;
- `BookingItem` не создаётся через booking API;
- тесты для `organizations`, `services` и `bookings` пока почти отсутствуют;
- конфигурация `settings.py`, Dockerfile и Compose-файл ориентированы на разработку, а не на production.

## Изменения в последней версии

### Гараж (Cars)
- ✅ Новое приложение `cars` с моделью `Car` (UUID PK)
- ✅ CRUD API `/api/cars/`: список, добавить, детали, редактировать, удалить
- ✅ Поле `cars` добавлено в ответы аутентификации (login/register) и в `/api/users/me/`
- ✅ Госномер уникален в рамках системы, автоматически приводится к верхнему регистру
- ✅ Валидация диаметра диска: 10–30 дюймов

### Пользователи
- ✅ Удалено поле `phone` из модели `User`, API и всех ответов
- ✅ Поиск в бронированиях переведён с `user__phone` на `user__email`
- ✅ Исправлен сломанный `UserSessionSerializer` (удалён как мёртвый код)
- ✅ Удалены дублированные функции в `email_auth_views.py`

### Организации
- ✅ Добавлена система заявок на подключение к агрегатору
- ✅ Новые поля: `shortName`, `organizationType`, `organizationStatus`, `organizationDateApproved`
- ✅ Государственные данные: `orgInn`, `orgOgrn`, `orgKpp`
- ✅ Поддержка диаметров дисков для шиномонтажа: `wheelDiameters`
- ✅ API для аппрува/деаппрува заявок администратором
- ✅ Удалена роль `ORGANIZATION` - владельцы имеют роль `CLIENT`

### Услуги
- ✅ Добавлено поле `status` для скрытия услуг ('active'/'ghost')
- ✅ Возможность редактирования услуг владельцами организаций
- ✅ Обновленная логика видимости для клиентов

### Бронирования
- ✅ Добавлены поля `carModel` и `wheelDiameter`
- ✅ Поддержка формата invoices для фронтенда
- ✅ Исправлена логика отображения для владельцев организаций
- ✅ Исправлена проблема с refresh token endpoint
- ✅ Обновленные права доступа без привязки к роли `ORGANIZATION`
- ✅ Специальный endpoint для отмены бронирований `POST /api/bookings/{id}/cancel/`
- ✅ Календарный формат данных `GET /api/bookings/calendar/`
- ✅ Логика отмены с проверкой прав (клиент/организация/администратор)

### Аутентификация и токены
- ✅ Добавлен публичный refresh endpoint `/api/token/refresh/`
- ✅ Исправлена проблема с middleware, который блокировал refresh запросы
- ✅ Refresh token теперь можно использовать для получения нового access token

## Связанные документы

- [README.md](README.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [DOCKER_SETUP.md](DOCKER_SETUP.md)

## Примеры использования

### Сценарий 1: Подача заявки на подключение организации

1. **Создание заявки клиентом:**
```http
POST /api/organizations/
Authorization: Bearer <client_token>
Content-Type: application/json

{
  "name": "Автомойка Блеск",
  "shortName": "АБ",
  "organizationType": "wash",
  "city": 1,
  "address": "ул. Гагарина, 50",
  "phone": "+79171234567",
  "email": "info@blesk.ru",
  "description": "Современная автомойка с качественным сервисом",
  "orgInn": "631234567890",
  "orgOgrn": "123456789012345",
  "orgKpp": "631201001"
}
```

2. **Администратор просматривает заявки:**
```http
GET /api/organizations/pending/
Authorization: Bearer <admin_token>
```

3. **Одобрение заявки:**
```http
POST /api/organizations/5/approve/
Authorization: Bearer <admin_token>
```

### Сценарий 2: Управление услугами организации

1. **Создание активной услуги:**
```http
POST /api/services/
Authorization: Bearer <owner_token>

{
  "organization": 5,
  "title": "Комплексная мойка",
  "description": "Мойка кузова + салон + коврики",
  "price": "800.00",
  "duration": 45,
  "status": "active"
}
```

2. **Создание скрытой VIP услуги:**
```http
POST /api/services/
Authorization: Bearer <owner_token>

{
  "organization": 5,
  "title": "VIP детейлинг",
  "description": "Премиум услуга для особых клиентов",
  "price": "3000.00",
  "duration": 180,
  "status": "ghost"
}
```

### Сценарий 3: Бронирование с информацией об автомобиле

```http
POST /api/bookings/
Authorization: Bearer <client_token>

{
  "service": 10,
  "scheduled_at": "2026-03-25T14:00:00Z",
  "carModel": "BMW X5",
  "wheelDiameter": 19
}
```

### Сценарий 4: Просмотр бронирований владельцем организации

```http
GET /api/bookings/?service__organization__owner=me
Authorization: Bearer <owner_token>
```

Владелец увидит все бронирования на услуги своих организаций плюс свои собственные бронирования как клиент.

### Сценарий 5: Календарь бронирований для организации

```http
GET /api/bookings/calendar/?status=NEW,CONFIRMED&ordering=scheduled_at
Authorization: Bearer <owner_token>
```

Ответ в формате invoices:

```json
{
  "count": 2,
  "results": [
    {
      "id": 10,
      "customerName": "Иван Петров",
      "dateTime": "25/03/2026 14:00",
      "carModel": "BMW X5",
      "serviceMethod": "Комплексная мойка",
      "duration": "45",
      "price": "800.00"
    },
    {
      "id": 11,
      "customerName": "Мария Сидорова",
      "dateTime": "25/03/2026 15:00",
      "carModel": "Toyota Camry",
      "serviceMethod": "Экспресс мойка",
      "duration": "30",
      "price": "500.00"
    }
  ]
}
```

### Сценарий 6: Отмена бронирования клиентом

```http
POST /api/bookings/10/cancel/
Authorization: Bearer <client_token>
```

Ответ:

```json
{
  "message": "Бронирование успешно отменено",
  "cancelled_by": "client",
  "old_status": "NEW",
  "booking": {
    "id": 10,
    "status": "CANCELLED",
    "customerName": "Иван Петров",
    "dateTime": "25/03/2026 14:00",
    ...
  }
}
```

### Сценарий 7: Отмена бронирования организацией

```http
POST /api/bookings/11/cancel/
Authorization: Bearer <owner_token>
```

Организация может отменить любое бронирование на свои услуги:

```json
{
  "message": "Бронирование успешно отменено",
  "cancelled_by": "organization",
  "old_status": "CONFIRMED",
  "booking": {
    "id": 11,
    "status": "CANCELLED",
    ...
  }
}
```

### Сценарий 8: Подтверждение бронирования организацией

```http
POST /api/bookings/12/confirm/
Authorization: Bearer <owner_token>
```

Организация может подтвердить новое бронирование (NEW → CONFIRMED):

```json
{
  "message": "Бронирование успешно подтверждено",
  "confirmed_by": "organization",
  "old_status": "NEW",
  "booking": {
    "id": 12,
    "status": "CONFIRMED",
    "customerName": "Петр Иванов",
    "dateTime": "26/03/2026 10:00",
    ...
  }
}
```

Ошибки:
- 403: Нет прав (только организация или админ)
- 400: Нельзя подтвердить бронирование с другим статусом (только NEW)

### Сценарий 9: Завершение бронирования организацией

```http
POST /api/bookings/13/complete/
Authorization: Bearer <owner_token>
```

Организация может завершить подтвержденное бронирование (CONFIRMED → DONE):

```json
{
  "message": "Бронирование успешно завершено",
  "completed_by": "organization",
  "old_status": "CONFIRMED",
  "booking": {
    "id": 13,
    "status": "DONE",
    "customerName": "Анна Смирнова",
    "dateTime": "25/03/2026 16:00",
    ...
  }
}
```

Ошибки:
- 403: Нет прав (только организация или админ)
- 400: Нельзя завершить бронирование с другим статусом (только CONFIRMED)

## Переходы статусов бронирований

```
NEW → CONFIRMED (подтверждение организацией)
NEW → CANCELLED (отмена клиентом/организацией/админом)

CONFIRMED → DONE (завершение организацией)
CONFIRMED → CANCELLED (отмена клиентом/организацией/админом)

CANCELLED - финальный статус
DONE - финальный статус
```

Доступные действия:
- `POST /api/bookings/{id}/confirm/` - подтверждение (организация, админ)
- `POST /api/bookings/{id}/complete/` - завершение (организация, админ)
- `POST /api/bookings/{id}/cancel/` - отмена (клиент, организация, админ)


---

## Управление расписанием и доступными слотами

### Обзор

Система управления временем работы организаций и доступными слотами для записи включает:

- **Расписание организаций** - рабочие дни, время работы, перерывы, длительность слотов
- **Выходные дни** - праздники и нерабочие дни
- **Доступность услуг** - специфичное расписание для отдельных услуг
- **Доступные слоты** - автоматическая генерация свободных слотов с учетом всех ограничений

### Расписание организаций

#### Получить расписание

```http
GET /api/organizations/schedules/
Authorization: Bearer <access_token>
```

Фильтры:
- `organization` - ID организации
- `weekday` - день недели (0-6, где 0 = понедельник)
- `is_working_day` - рабочий день (true/false)
- `is_active` - активно (true/false)

Ответ:

```json
{
  "count": 7,
  "results": [
    {
      "id": 1,
      "organization": 5,
      "weekday": 0,
      "weekday_display": "Понедельник",
      "is_working_day": true,
      "open_time": "09:00:00",
      "close_time": "18:00:00",
      "break_start": "13:00:00",
      "break_end": "14:00:00",
      "slot_duration": 30,
      "is_active": true,
      "created_at": "2026-03-19T10:00:00Z",
      "updated_at": "2026-03-19T10:00:00Z"
    }
  ]
}
```

#### Создать расписание

```http
POST /api/organizations/schedules/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "organization": 5,
  "weekday": 0,
  "is_working_day": true,
  "open_time": "09:00",
  "close_time": "18:00",
  "break_start": "13:00",
  "break_end": "14:00",
  "slot_duration": 30
}
```

Правила:
- Владелец может создавать расписание только для своих организаций
- ADMIN может создавать для любых организаций
- `weekday` - уникален для организации (0-6)
- `open_time` должно быть раньше `close_time`
- `break_start` и `break_end` должны быть в рабочее время
- `slot_duration` - от 5 до 240 минут

#### Обновить расписание

```http
PATCH /api/organizations/schedules/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "open_time": "08:00",
  "close_time": "20:00"
}
```

#### Удалить расписание

```http
DELETE /api/organizations/schedules/{id}/
Authorization: Bearer <access_token>
```

### Выходные дни

#### Получить выходные

```http
GET /api/organizations/holidays/
Authorization: Bearer <access_token>
```

Фильтры:
- `organization` - ID организации
- `date` - дата (YYYY-MM-DD)
- `is_active` - активно (true/false)

Ответ:

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "organization": 5,
      "date": "2026-05-01",
      "reason": "Праздник труда",
      "is_active": true,
      "created_at": "2026-03-19T10:00:00Z"
    }
  ]
}
```

#### Создать выходной день

```http
POST /api/organizations/holidays/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "organization": 5,
  "date": "2026-05-01",
  "reason": "Праздник труда"
}
```

Правила:
- Владелец может создавать выходные только для своих организаций
- ADMIN может создавать для любых организаций
- Комбинация `organization` + `date` уникальна

### Доступность услуг

Специфичное расписание для отдельных услуг (переопределяет общее расписание организации).

#### Получить правила доступности

```http
GET /api/organizations/service-availability/
Authorization: Bearer <access_token>
```

Фильтры:
- `service` - ID услуги
- `weekday` - день недели (0-6)
- `is_active` - активно (true/false)

Ответ:

```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "service": 10,
      "service_title": "Шиномонтаж R16",
      "weekday": 0,
      "weekday_display": "Понедельник",
      "available_from": "10:00:00",
      "available_to": "17:00:00",
      "max_bookings_per_slot": 2,
      "is_active": true,
      "created_at": "2026-03-19T10:00:00Z"
    }
  ]
}
```

#### Создать правило доступности

```http
POST /api/organizations/service-availability/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "service": 10,
  "weekday": 0,
  "available_from": "10:00",
  "available_to": "17:00",
  "max_bookings_per_slot": 2
}
```

Правила:
- Владелец может создавать правила только для услуг своих организаций
- ADMIN может создавать для любых услуг
- Комбинация `service` + `weekday` уникальна
- `available_from` должно быть раньше `available_to`
- `max_bookings_per_slot` - от 1 до 10

### Доступные слоты

Получение списка доступных слотов для записи на услугу.

#### Получить доступные слоты

```http
GET /api/organizations/available-slots/for_service/?service_id=10&date=2026-03-25
Authorization: Bearer <access_token>
```

Query параметры:
- `service_id` (обязательно) - ID услуги
- `date` (обязательно) - дата в формате YYYY-MM-DD

Ответ:

```json
{
  "service_id": 10,
  "service_title": "Шиномонтаж R16",
  "organization": "Шиномонтаж на Ленина",
  "date": "2026-03-25",
  "duration": 60,
  "slots": [
    {
      "time": "09:00",
      "datetime": "2026-03-25T09:00:00",
      "available": true,
      "booked": 0,
      "capacity": 1
    },
    {
      "time": "09:30",
      "datetime": "2026-03-25T09:30:00",
      "available": true,
      "booked": 0,
      "capacity": 1
    },
    {
      "time": "10:00",
      "datetime": "2026-03-25T10:00:00",
      "available": false,
      "booked": 1,
      "capacity": 1
    }
  ]
}
```

Логика генерации слотов:

1. Проверяется, не выходной ли день (holidays)
2. Получается расписание организации для дня недели
3. Проверяется специфичное расписание услуги (если есть)
4. Генерируются слоты с учетом:
   - Рабочего времени
   - Перерывов
   - Длительности услуги
   - Минимального времени до записи (1 час от текущего момента)
   - Существующих бронирований
   - Максимального количества записей на слот

Ошибки:

```json
// Отсутствуют параметры
{
  "error": "Требуются параметры service_id и date"
}

// Услуга не найдена
{
  "error": "Услуга не найдена"
}

// Неверный формат даты
{
  "error": "Неверный формат даты. Используйте YYYY-MM-DD"
}

// Прошедшая дата
{
  "error": "Нельзя записаться на прошедшую дату"
}
```

### Валидация при создании бронирования

При создании или обновлении бронирования автоматически проверяется:

1. **Время не в прошлом** - нельзя записаться на прошедшее время
2. **Минимальное время** - минимум 1 час от текущего момента
3. **Выходной день** - организация не работает в этот день
4. **Расписание** - организация работает в этот день недели
5. **Рабочее время** - время попадает в рабочие часы
6. **Перерыв** - время не попадает на перерыв
7. **Доступность услуги** - услуга доступна в это время (если есть специфичное расписание)
8. **Занятость слота** - слот не занят другими бронированиями

Примеры ошибок:

```json
// Прошедшее время
{
  "scheduled_at": ["Нельзя записаться на прошедшее время"]
}

// Слишком рано
{
  "scheduled_at": ["Минимальное время до записи - 1 час"]
}

// Выходной
{
  "scheduled_at": ["Организация не работает 01.05.2026"]
}

// Нерабочий день
{
  "scheduled_at": ["Организация не работает в этот день недели"]
}

// Вне рабочего времени
{
  "scheduled_at": ["Организация работает с 09:00 до 18:00"]
}

// Перерыв
{
  "scheduled_at": ["Время попадает на перерыв (13:00 - 14:00)"]
}

// Услуга недоступна
{
  "scheduled_at": ["Услуга доступна с 10:00 до 17:00"]
}

// Слот занят
{
  "scheduled_at": ["Это время уже занято"]
}
```

### Примеры использования

#### 1. Настройка расписания для новой организации

```javascript
// Создаем расписание на всю неделю
const weekdays = [
  { day: 0, name: 'Понедельник' },
  { day: 1, name: 'Вторник' },
  { day: 2, name: 'Среда' },
  { day: 3, name: 'Четверг' },
  { day: 4, name: 'Пятница' },
  { day: 5, name: 'Суббота' },
  { day: 6, name: 'Воскресенье' }
];

for (const { day } of weekdays) {
  const isWorkingDay = day < 6; // Пн-Сб рабочие
  
  await fetch('http://localhost:8000/api/organizations/schedules/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      organization: 5,
      weekday: day,
      is_working_day: isWorkingDay,
      open_time: isWorkingDay ? '09:00' : '10:00',
      close_time: isWorkingDay ? '18:00' : '16:00',
      break_start: '13:00',
      break_end: '14:00',
      slot_duration: 30
    })
  });
}
```

#### 2. Добавление праздничных дней

```javascript
const holidays = [
  { date: '2026-05-01', reason: 'Праздник труда' },
  { date: '2026-05-09', reason: 'День Победы' },
  { date: '2026-06-12', reason: 'День России' }
];

for (const holiday of holidays) {
  await fetch('http://localhost:8000/api/organizations/holidays/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      organization: 5,
      ...holiday
    })
  });
}
```

#### 3. Настройка специального расписания для услуги

```javascript
// Шиномонтаж доступен только в определенные часы
await fetch('http://localhost:8000/api/organizations/service-availability/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    service: 10,
    weekday: 0, // Понедельник
    available_from: '10:00',
    available_to: '17:00',
    max_bookings_per_slot: 2 // Можно записать 2 клиентов одновременно
  })
});
```

#### 4. Получение доступных слотов и создание бронирования

```javascript
// 1. Получаем доступные слоты
const response = await fetch(
  'http://localhost:8000/api/organizations/available-slots/for_service/?service_id=10&date=2026-03-25',
  {
    headers: {
      'Authorization': `Bearer ${access_token}`
    }
  }
);

const data = await response.json();
console.log('Доступные слоты:', data.slots);

// 2. Выбираем свободный слот
const availableSlot = data.slots.find(slot => slot.available);

// 3. Создаем бронирование
await fetch('http://localhost:8000/api/bookings/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    service: 10,
    scheduled_at: availableSlot.datetime,
    car_model: 'Lada Vesta',
    wheel_diameter: 16
  })
});
```

### Права доступа

| Действие | CLIENT (владелец) | CLIENT (обычный) | ADMIN |
|----------|-------------------|------------------|-------|
| Просмотр расписания | Свои организации | Нет | Все |
| Создание расписания | Свои организации | Нет | Все |
| Редактирование расписания | Свои организации | Нет | Все |
| Удаление расписания | Свои организации | Нет | Все |
| Просмотр выходных | Свои организации | Нет | Все |
| Создание выходных | Свои организации | Нет | Все |
| Просмотр доступности услуг | Свои организации | Нет | Все |
| Создание доступности услуг | Свои организации | Нет | Все |
| Просмотр доступных слотов | Да | Да | Да |

### Рекомендации

1. **Создавайте расписание сразу после создания организации** - без расписания клиенты не смогут записаться
2. **Используйте slot_duration кратный длительности услуг** - это упростит планирование
3. **Настраивайте max_bookings_per_slot для услуг, которые можно выполнять параллельно** - например, несколько постов шиномонтажа
4. **Добавляйте праздничные дни заранее** - клиенты увидят, что организация не работает
5. **Используйте endpoint available-slots перед созданием бронирования** - это покажет клиенту только доступные слоты

---
