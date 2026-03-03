# Docker Setup - Pioneer Backend

## Быстрый старт

### 1. Запуск проекта

```bash
docker-compose up --build
```

Это запустит:
- PostgreSQL на порту 5433
- Django на порту 8000

### 2. Доступ к приложению

- API: http://localhost:8000/api/
- Админка: http://localhost:8000/admin/

### 3. Вход в админку

Email: `admin@pioneer.local`
Код: `4444` (в dev режиме)

## Конфигурация

### Переменные окружения (.env.docker)

```env
# Django
DEBUG=True
SECRET_KEY=super-secret-key...

# Database
DB_NAME=pioneer
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Email (Яндекс SMTP)
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=Dmitry4424@yandex.ru
EMAIL_HOST_PASSWORD=mhbjhqtgkugfrwpl
DEFAULT_FROM_EMAIL=Dmitry4424@yandex.ru
```

## Команды

### Запуск контейнеров
```bash
docker-compose up
```

### Запуск в фоновом режиме
```bash
docker-compose up -d
```

### Остановка контейнеров
```bash
docker-compose down
```

### Пересборка образов
```bash
docker-compose up --build
```

### Просмотр логов
```bash
docker-compose logs -f web
docker-compose logs -f db
```

### Выполнение команд в контейнере
```bash
# Django shell
docker-compose exec web python manage.py shell

# Создать миграции
docker-compose exec web python manage.py makemigrations

# Применить миграции
docker-compose exec web python manage.py migrate

# Создать суперпользователя
docker-compose exec web python manage.py shell
>>> from users.models import User
>>> User.objects.create_superuser('newemail@example.com')
```

### Доступ к базе данных
```bash
# Подключиться к PostgreSQL
docker-compose exec db psql -U postgres -d pioneer

# Или с хоста
psql -h localhost -p 5433 -U postgres -d pioneer
```

## Entrypoint

При запуске контейнера автоматически выполняется:

1. Ожидание готовности базы данных
2. Применение миграций
3. Создание суперпользователя (если не существует)
4. Запуск сервера

## Volumes

- `pioneer_pgdata` - данные PostgreSQL (сохраняются между перезапусками)
- `.:/app` - код проекта (изменения применяются сразу)

## Порты

- `8000` - Django (web)
- `5433` - PostgreSQL (db) - маппится на 5433 чтобы не конфликтовать с локальным PostgreSQL

## Troubleshooting

### База данных не готова
Если видите ошибки подключения к БД, подождите пока PostgreSQL полностью запустится:
```bash
docker-compose logs db
```

### Миграции не применились
Примените миграции вручную:
```bash
docker-compose exec web python manage.py migrate
```

### Нужно пересоздать базу данных
```bash
docker-compose down -v  # Удалит volumes
docker-compose up --build
```

### Email не отправляются
Проверьте настройки в `.env.docker`:
```bash
docker-compose exec web python test_yandex_send.py
```

## Production

Для production окружения:

1. Измените `SECRET_KEY` на случайный
2. Установите `DEBUG=False`
3. Настройте `ALLOWED_HOSTS`
4. Используйте production SMTP
5. Используйте gunicorn вместо runserver
6. Настройте nginx для статики
7. Используйте SSL сертификаты

### Пример production entrypoint:

```bash
#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn pioneer_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

## Полезные ссылки

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
