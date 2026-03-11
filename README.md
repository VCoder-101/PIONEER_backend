# PIONEER Backend

Частично реализованный backend для web-приложения PIONEER на Django + Django REST Framework. Репозиторий уже содержит email-code аутентификацию, базовые CRUD API для организаций, услуг и бронирований, а также dev-конфигурацию для локального запуска и Docker.

Исходной правдой для этого репозитория является текущий код. Эта документация описывает именно фактическое состояние проекта, включая известные ограничения.

## Что есть в проекте

- backend для web-приложения, не mobile-only API;
- email-only аутентификация без паролей для публичного пользовательского потока;
- JWT access/refresh токены и серверная модель `UserSession`;
- доменные apps `users`, `organizations`, `services`, `bookings`;
- Django Admin с отдельным входом по email-коду;
- локальный dev setup и Docker Compose для разработки.

## Основные apps и сущности

### `users`

- `User`: email как логин, `name`, необязательный `phone`, роли `ADMIN` / `ORGANIZATION` / `CLIENT`, признак принятия privacy policy, текущие `device_id` и `session_id`.
- `UserSession`: серверная сессия устройства с `device_id`, `ip_address`, `user_agent`, `expires_at`, `is_active`.

### `organizations`

- `City`
- `Organization`: владелец (`owner -> users.User`), город, адрес, телефон, email, описание, `is_active`.

### `services`

- `Service`: организация, название, описание, цена, длительность, `is_active`.
- `ServiceItem`: дополнительный элемент услуги, цена, обязательность, порядок сортировки.

### `bookings`

- `Booking`: клиент, услуга, статус (`NEW`, `CONFIRMED`, `CANCELLED`, `DONE`), `scheduled_at`.
- `BookingItem`: выбранный `ServiceItem`, количество и цена на момент бронирования.

### `api`

- служебный app;
- management commands `seed_db` и `seed_demo`.

`seed_db` соответствует текущим email/role-моделям заметно лучше. `seed_demo` остаётся legacy-командой со старой phone/password логикой и не должен использоваться как источник актуального контракта.

## Роли

- `ADMIN`: полный доступ, управление пользователями и всеми доменными сущностями.
- `ORGANIZATION`: владелец организаций, услуг и просмотр бронирований по своим услугам.
- `CLIENT`: чтение активных организаций и услуг, создание и изменение своих бронирований.

Важно:

- публичная регистрация через API создаёт только пользователей с ролью `CLIENT`;
- роли `ORGANIZATION` и `ADMIN` появляются вне публичного регистрационного потока: через админку, management-команды или seed-данные.

## Аутентификация

Основной публичный auth flow сейчас такой:

1. `POST /api/users/auth/send-code/`
2. `POST /api/users/auth/verify-code/`
3. сохранить `jwt.access`, `jwt.refresh` и `session.id`
4. использовать `Authorization: Bearer <access_token>` для защищённых API
5. при выходе вызвать `POST /api/users/auth/logout/` с `session_id`

Особенности текущей реализации:

- авторизация идёт через email-коды, пароли в пользовательском API не используются;
- тип auth-потока определяется по состоянию пользователя в БД:
  - нет пользователя -> регистрация;
  - пользователь есть и `name` заполнено -> логин;
  - пользователь есть, но `name` пустое -> завершение регистрации;
- в dev-режиме send-code endpoints могут возвращать `dev_code`, а проверка кода принимает `4444`;
- в коде остаются legacy/specialized auth routes:
  - `/api/users/auth/email/register/*`
  - `/api/users/auth/email/login/*`
  - `/api/users/auth/recovery/*`
  - `/api/users/auth/jwt/verify/`
  - `/api/users/auth/logout/`

Подробности и примеры запросов: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Основные API-группы

- `/api/users/auth/*` — публичная аутентификация, recovery, logout, JWT verify.
- `/api/users/` — admin-only user API, плюс `/api/users/me/` для текущего пользователя.
- `/api/organizations/` — организации.
- `/api/organizations/cities/` — города.
- `/api/services/` — услуги.
- `/api/services/items/` — элементы услуг.
- `/api/bookings/` — бронирования.

## Локальный запуск

### Требования

- Python 3.12
- PostgreSQL
- `pip`

### 1. Установка зависимостей

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка окружения

Проект читает переменные из `.env` через `python-dotenv`. Минимальный пример:

```env
DEBUG=True
SECRET_KEY=change-me

DB_NAME=pioneer
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

Замечания:

- в `pioneer_backend/settings.py` есть dev-friendly значения по умолчанию, но лучше задавать их явно;
- для основного send-code auth flow в `DEBUG=True` SMTP не обязателен, потому что dev-режим может вернуть `dev_code`;
- recovery flow и production-почта зависят от SMTP-настроек.

### 3. Подготовка базы

```sql
CREATE DATABASE pioneer;
```

### 4. Миграции и запуск

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

После запуска:

- API: `http://127.0.0.1:8000/api/`
- админка: `http://127.0.0.1:8000/admin/`

Важно: Django Admin в этом проекте логинится не паролем, а через отдельный email-code flow на `/admin/login/`.

## Запуск через Docker

Текущий `docker-compose.yml` — это dev-конфигурация.

### Быстрый старт

```bash
docker compose up --build
```

Что делает текущий `docker/entrypoint.sh`:

1. ждёт готовности PostgreSQL;
2. применяет миграции;
3. создаёт superuser `admin@pioneer.local`, если его ещё нет;
4. запускает `python manage.py runserver 0.0.0.0:8000`.

После старта:

- API: `http://127.0.0.1:8000/api/`
- админка: `http://127.0.0.1:8000/admin/`
- PostgreSQL с хоста: `127.0.0.1:5433`

### Полезные команды

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_db
docker compose logs -f web
docker compose down
docker compose down -v
```

Используйте `seed_db`, если нужны тестовые организации, услуги, клиенты и бронирования. Не используйте `seed_demo` как текущий сценарий авторизации: он основан на старой phone/password модели.

Подробности: [DOCKER_SETUP.md](DOCKER_SETUP.md)

## Что важно знать про текущее состояние

- проект уже не пустой, но это всё ещё не production-ready backend;
- `TIME_ZONE` в настройках сейчас `UTC`;
- `DEBUG=True`, `ALLOWED_HOSTS=[]` и `CORS_ALLOW_ALL_ORIGINS=True` делают текущую конфигурацию dev-only;
- `docker-compose.yml` и `Dockerfile` подходят для локальной разработки, а не для production-развёртывания;
- refresh token выдаётся в auth-ответах, но публичный endpoint вида `/api/token/refresh/` в `pioneer_backend/urls.py` сейчас не подключён;
- booking flow пока базовый: нет публичного API слотов, проверки конфликтов записи, action-endpoints для статусов и полноценного create-flow для `BookingItem`;
- write-права вокруг `ServiceItem` пока не доведены до строгой role-based модели;
- автотесты в основном есть только в `users/tests.py`, а тесты `organizations`, `services`, `bookings` пока пустые.

## Документация

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — актуальные endpoints, auth flow, payloads и ограничения.
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) — фактические модели и связи.
- [DOCKER_SETUP.md](DOCKER_SETUP.md) — dev Docker setup.
- [PLAN.md](PLAN.md) — рабочий план доработки проекта.
