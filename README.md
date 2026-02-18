# Pioneer Backend

Monolith + Domain Apps архитектура для системы бронирования услуг.

## 🎯 О проекте

Pioneer Backend - это RESTful API для системы бронирования услуг с поддержкой:
- Управления организациями и их услугами
- Бронирования услуг клиентами
- Ролевой модели доступа (ADMIN, OWNER, CLIENT)
- Элементов услуг (опций и дополнений)

## 📋 Требования

- Python 3.12+
- PostgreSQL 18+
- pip

## 🚀 Быстрый старт

### 1. Клонирование и установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных

Создать базу данных PostgreSQL:
```sql
CREATE DATABASE pioneer;
```

Настроить `.env` файл (уже создан):
```env
DEBUG=True
SECRET_KEY=super-secret-key
DB_NAME=pioneer
DB_USER=postgres
DB_PASSWORD=admin123
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 3. Миграции и запуск

```bash
# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

## 📚 Документация

- [API Documentation](API_DOCUMENTATION.md) - Полная документация API
- [Database Schema](DATABASE_SCHEMA.md) - Схема базы данных
- [TZ Checklist](TZ_CHECKLIST.md) - Чек-лист выполнения ТЗ
- [Changelog](CHANGELOG.md) - История изменений

## 🏗️ Архитектура

### Доменные приложения

#### 1. Users — Пользователи
- Аутентификация по email
- Роли (ADMIN / OWNER / CLIENT)
- Сессии пользователей
- Профиль пользователя

#### 2. Organizations — Организации
- Организации владельцев
- Города
- Связь: User (OWNER) → Organization

#### 3. Services — Услуги
- Услуги организаций
- Элементы услуг (опции, дополнения)
- Цена, длительность, описание
- Связь: Organization → Services → ServiceItems

#### 4. Bookings — Бронирования
- Бронирования услуг
- Элементы бронирования
- Статусы: NEW / CONFIRMED / CANCELLED / DONE
- Связи: User + Service → Booking → BookingItems

## 🔗 API Endpoints

### Аутентификация
```
POST   /api/users/register/     - Регистрация
GET    /api/users/me/           - Текущий пользователь
```

### Пользователи (ADMIN)
```
GET    /api/users/              - Список пользователей
GET    /api/users/{id}/         - Получить пользователя
```

### Города
```
GET    /api/organizations/cities/     - Список городов
```

### Организации
```
GET    /api/organizations/            - Список организаций
POST   /api/organizations/            - Создать организацию
GET    /api/organizations/{id}/       - Получить организацию
PUT    /api/organizations/{id}/       - Обновить организацию
DELETE /api/organizations/{id}/       - Удалить организацию
```

### Услуги
```
GET    /api/services/                 - Список услуг
POST   /api/services/                 - Создать услугу
GET    /api/services/{id}/            - Получить услугу
PUT    /api/services/{id}/            - Обновить услугу
DELETE /api/services/{id}/            - Удалить услугу
```

### Элементы услуг
```
GET    /api/services/items/           - Список элементов
POST   /api/services/items/           - Создать элемент
GET    /api/services/items/{id}/      - Получить элемент
PUT    /api/services/items/{id}/      - Обновить элемент
DELETE /api/services/items/{id}/      - Удалить элемент
```

### Бронирования
```
GET    /api/bookings/                 - Список бронирований
POST   /api/bookings/                 - Создать бронирование
GET    /api/bookings/{id}/            - Получить бронирование
PUT    /api/bookings/{id}/            - Обновить бронирование
DELETE /api/bookings/{id}/            - Удалить бронирование
```

## 🔐 Роли и права доступа

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

## 🗄️ База данных

### Таблицы
- **User** - пользователи с ролями
- **UserSession** - сессии пользователей
- **City** - города
- **Organization** - организации
- **Service** - услуги
- **ServiceItem** - элементы услуг
- **Booking** - бронирования
- **BookingItem** - элементы бронирований

### Индексы
- 47+ индексов для оптимизации запросов
- Все внешние ключи индексированы
- Составные индексы для частых запросов

Подробнее: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

## 🛠️ Технологии

- **Django 6.0.2** - Web framework
- **Django REST Framework 3.16.1** - REST API
- **PostgreSQL 18** - База данных
- **psycopg2-binary 2.9.11** - PostgreSQL adapter
- **django-filter 25.2** - Фильтрация API
- **django-cors-headers 4.9.0** - CORS
- **python-dotenv 1.2.1** - Переменные окружения

## 📦 Структура проекта

```
pioneer_backend/
├── users/                  # Пользователи, роли, сессии
├── organizations/          # Организации и города
├── services/              # Услуги и их элементы
├── bookings/              # Бронирования
├── pioneer_backend/       # Настройки проекта
├── .env                   # Переменные окружения
├── requirements.txt       # Зависимости
├── manage.py             # Django management
├── README.md             # Этот файл
├── API_DOCUMENTATION.md  # Документация API
├── DATABASE_SCHEMA.md    # Схема БД
├── TZ_CHECKLIST.md       # Чек-лист ТЗ
├── CHANGELOG.md          # История изменений
└── SUMMARY.md            # Сводка работ
```

## 🧪 Команды разработки

```bash
# Проверка проекта
python manage.py check

# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver

# Запуск shell
python manage.py shell
```

## 📝 Примеры использования

### Регистрация клиента
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@example.com",
    "password": "password123",
    "role": "CLIENT"
  }'
```

### Создание организации (OWNER)
```bash
curl -X POST http://127.0.0.1:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{
    "name": "Салон красоты",
    "city": 1,
    "address": "ул. Ленина, 1",
    "phone": "+7 (999) 123-45-67"
  }'
```

### Создание бронирования (CLIENT)
```bash
curl -X POST http://127.0.0.1:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{
    "service": 1,
    "scheduled_at": "2026-02-20T14:00:00Z",
    "status": "NEW"
  }'
```

## ✅ Выполнение ТЗ

- ✅ Таблица пользователей с необходимыми полями и ограничениями
- ✅ Таблица сессий пользователей с индексами
- ✅ Механизм хранения и назначения ролей
- ✅ Таблица городов со связями
- ✅ Таблица организаций с полями и связями
- ✅ Таблица сервисов
- ✅ Таблица элементов сервисов со связями
- ✅ Индексы на всех ключевых полях для оптимизации

Подробнее: [TZ_CHECKLIST.md](TZ_CHECKLIST.md)

## 🔮 Будущие улучшения

- [ ] JWT аутентификация
- [ ] Swagger/OpenAPI документация
- [ ] Unit и integration тесты
- [ ] Docker контейнеризация
- [ ] CI/CD pipeline
- [ ] WebSockets для real-time уведомлений
- [ ] Email уведомления
- [ ] Интеграция платежных систем
- [ ] Кэширование (Redis)
- [ ] Логирование и мониторинг

## 📄 Лицензия

Этот проект создан в учебных целях.

## 👥 Контакты

Для вопросов и предложений создавайте issue в репозитории.

