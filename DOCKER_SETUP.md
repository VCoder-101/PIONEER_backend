# Docker Setup - PIONEER Backend

Текущий Docker setup предназначен для локальной разработки, а не для production.

## Что поднимается

`docker-compose.yml` описывает два сервиса:

- `db` — `postgres:18`, порт хоста `5433 -> 5432`
- `web` — Django приложение на порту `8000`

Используемые volumes:

- `pioneer_pgdata` — данные PostgreSQL
- `.:/app` — bind mount исходников внутрь контейнера `web`

## Быстрый старт

```bash
docker compose up --build
```

После запуска:

- API: `http://127.0.0.1:8000/api/`
- админка: `http://127.0.0.1:8000/admin/`
- PostgreSQL с хоста: `127.0.0.1:5433`

## Что делает entrypoint

Файл `docker/entrypoint.sh` при старте контейнера:

1. ждёт доступности PostgreSQL;
2. выполняет `python manage.py migrate --noinput`;
3. создаёт superuser `admin@pioneer.local`, если он ещё отсутствует;
4. запускает `python manage.py runserver 0.0.0.0:8000`.

Это означает, что текущий Docker setup:

- уже применяет миграции автоматически;
- ориентирован на разработку;
- использует `runserver`, а не production WSGI-сервер.

## Переменные окружения

Контейнер `web` читает `.env.docker`.

Минимально важные переменные:

```env
DEBUG=True
SECRET_KEY=change-me

DB_NAME=pioneer
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

Дополнительно в `.env.docker` могут быть SMTP-параметры для email-отправки.

Важно:

- не используйте dev-секреты и dev SMTP credentials как production-конфигурацию;
- при `DEBUG=True` основные auth send-code endpoints могут возвращать `dev_code`, поэтому для локальной разработки SMTP не всегда обязателен.

## Полезные команды

### Запуск

```bash
docker compose up
docker compose up -d
docker compose up --build
```

### Остановка

```bash
docker compose down
docker compose down -v
```

`down -v` удалит volume PostgreSQL и все данные внутри Docker-базы.

### Логи

```bash
docker compose logs -f web
docker compose logs -f db
```

### Django-команды внутри контейнера

```bash
docker compose exec web python manage.py shell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_db
```

Используйте `seed_db`, если нужны тестовые организации, услуги, клиенты и бронирования.

Не используйте `seed_demo` как актуальный сценарий инициализации: эта команда осталась от старой phone/password модели.

### Доступ к базе

```bash
docker compose exec db psql -U postgres -d pioneer
```

Или с хоста:

```bash
psql -h 127.0.0.1 -p 5433 -U postgres -d pioneer
```

## Вход в админку

Текущая админка использует кастомный email-code login:

- URL: `http://127.0.0.1:8000/admin/login/`
- пользователь по умолчанию: `admin@pioneer.local`

В dev-режиме:

- send-code flow может вернуть `dev_code` в API;
- verify логика принимает код `4444`.

## Типичный dev workflow

1. `docker compose up --build`
2. открыть `http://127.0.0.1:8000/admin/` или `http://127.0.0.1:8000/api/`
3. при необходимости наполнить базу через `docker compose exec web python manage.py seed_db`
4. смотреть логи через `docker compose logs -f web`

## Ограничения текущего Docker setup

- это не production-compose;
- `DEBUG=True` и `runserver` остаются dev-only настройками;
- нет `nginx`, `gunicorn`, `collectstatic`, HTTPS и отдельного production-контура;
- secrets и SMTP-конфигурацию нужно выносить из репозитория перед реальным деплоем.

## Связанные документы

- [README.md](README.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
