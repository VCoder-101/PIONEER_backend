# API Documentation - PIONEER Backend

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

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ..."
}
```

Ответ:

```json
{
  "access": "eyJ..."
}
```

Важно:
- Refresh endpoint НЕ требует Bearer токена в заголовке
- Отправляется только refresh token в теле запроса
- Возвращается новый access token
- Refresh token остается действительным до истечения срока (30 дней)

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

Роутер также даёт:

- `GET /api/organizations/{id}/`
- `PUT /api/organizations/{id}/`
- `PATCH /api/organizations/{id}/`
- `DELETE /api/organizations/{id}/`

## Services API

### Services

Доступ:

- `ADMIN` — все услуги;
- Владельцы организаций — услуги своих организаций;
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

- `user__phone` - по телефону клиента
- `service__title` - по названию услуги

Сортировка:

- `scheduled_at` - по времени записи
- `created_at` - по дате создания

### Создать бронирование

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
- `carModel` - модель автомобиля
- `wheelDiameter` - диаметр диска

Особенности текущей реализации:

- `perform_create()` всегда подставляет `user = request.user`;
- `status` можно передать сразу, если он соответствует choices модели;
- API пока не создаёт `BookingItem` через booking payload;
- нет проверки слотов, конфликтов времени и строгих переходов статусов.

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
