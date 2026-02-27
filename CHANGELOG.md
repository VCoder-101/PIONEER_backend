# История изменений Pioneer Backend

# История изменений Pioneer Backend

## 2026-02-18 - Добавлены недостающие таблицы согласно ТЗ

### Новые модели

#### Cities (Города)
- ✅ `organizations/models.py` - модель City
- Поля: name, region, country, is_active, created_at
- Индексы: name, is_active
- API: GET /api/organizations/cities/ (только чтение)

#### ServiceItems (Элементы услуг)
- ✅ `services/models.py` - модель ServiceItem
- Поля: service, name, description, price, is_required, is_active, order
- Связь: Service 1 → N ServiceItem
- Индексы: service + is_active, order
- API: CRUD /api/services/items/

#### BookingItems (Элементы бронирования)
- ✅ `bookings/models.py` - модель BookingItem
- Поля: booking, service_item, quantity, price
- Связь: Booking 1 → N BookingItem
- Индексы: booking
- Автоматически включается в Booking через inline

#### UserSessions (Сессии пользователей)
- ✅ `users/models.py` - модель UserSession
- Поля: user, session_key, ip_address, user_agent, created_at, expires_at, is_active
- Индексы: user + is_active, session_key, expires_at + is_active
- Для отслеживания активных сессий пользователей

### Обновленные модели

#### Organization
- Добавлены поля: city (FK), address, phone, email, description, is_active
- Индексы: owner + is_active, city + is_active, created_at

#### Service
- Добавлена связь с ServiceItem (items)
- Индексы: organization + is_active, is_active + price, created_at

#### Booking
- Добавлено поле: updated_at
- Добавлена связь с BookingItem (items)
- Индексы: user + status, service + status, status + scheduled_at, created_at

#### User
- Добавлено поле: last_login
- Индексы: email, role + is_active, created_at

### Индексы базы данных
Все ключевые поля имеют индексы для оптимизации запросов:
- Внешние ключи (FK): db_index=True
- Поля для фильтрации: status, is_active, role
- Поля для сортировки: created_at, price, scheduled_at
- Составные индексы через Meta.indexes

### API Endpoints
Добавлены новые endpoints:
- GET /api/organizations/cities/ - список городов
- CRUD /api/services/items/ - элементы услуг

### Admin панель
- Добавлены inline редакторы для ServiceItem и BookingItem
- Обновлены фильтры и поиск для всех моделей
- Добавлена админка для City и UserSession

---

## 2026-02-18 - Добавлена система авторизации и прав доступа

### Permissions (Права доступа)
- ✅ `users/permissions.py` - IsAdmin, IsOwner, IsClient, IsAdminOrOwner
- ✅ `organizations/permissions.py` - IsOrganizationOwner
- ✅ `services/permissions.py` - IsServiceOwner
- ✅ `bookings/permissions.py` - IsBookingOwnerOrServiceOwner

### Обновленные Views с контролем доступа
**Users:**
- Доступ только для ADMIN
- Добавлен endpoint `/api/users/register/` для регистрации (публичный)
- Добавлен endpoint `/api/users/me/` для получения профиля текущего пользователя

**Organizations:**
- ADMIN: видит все организации
- OWNER: видит только свои организации
- CLIENT: видит все (только чтение)
- Автоматическая установка owner при создании

**Services:**
- ADMIN: видит все услуги
- OWNER: видит и управляет услугами своих организаций
- CLIENT: видит только активные услуги (только чтение)
- Фильтрация: по organization, is_active
- Поиск: по title, description
- Сортировка: по price, created_at

**Bookings:**
- ADMIN: видит все бронирования
- OWNER: видит бронирования на услуги своих организаций
- CLIENT: видит только свои бронирования
- Автоматическая установка user при создании
- Фильтрация: по status, service
- Поиск: по user__email, service__title
- Сортировка: по scheduled_at, created_at

### Настройки DRF
- Добавлена аутентификация через сессии
- Включена пагинация (20 элементов на страницу)
- Установлен django-filter для фильтрации API
- Добавлены фильтры поиска и сортировки

### Зависимости
- Добавлен `django-filter==25.2` в requirements.txt

---

## 2026-02-18 - Инициализация проекта и настройка архитектуры

### Настройка окружения
- ✅ Создан `.env` файл с переменными окружения (БД, SECRET_KEY, DEBUG)
- ✅ Настроено подключение к PostgreSQL в `settings.py`
- ✅ Добавлен `python-dotenv` для работы с переменными окружения
- ✅ Настроена кодировка UTF-8 для PostgreSQL

### Архитектура: Monolith + Domain Apps

#### 1. Users (Пользователи)
**Файлы:**
- `users/models.py` - Кастомная модель User с логином по email
- `users/serializers.py` - UserSerializer, UserCreateSerializer
- `users/views.py` - UserViewSet
- `users/urls.py` - API endpoints для пользователей
- `users/admin.py` - Админ-панель для User

**Модель User:**
- email (unique, логин)
- password
- role (ADMIN / OWNER / CLIENT)
- is_active
- created_at

#### 2. Organizations (Организации)
**Файлы:**
- `organizations/models.py` - Модель Organization
- `organizations/serializers.py` - OrganizationSerializer
- `organizations/views.py` - OrganizationViewSet
- `organizations/urls.py` - API endpoints для организаций
- `organizations/admin.py` - Админ-панель для Organization

**Модель Organization:**
- name
- owner (FK → User)
- created_at

#### 3. Services (Услуги)
**Файлы:**
- `services/models.py` - Модель Service
- `services/serializers.py` - ServiceSerializer
- `services/views.py` - ServiceViewSet
- `services/urls.py` - API endpoints для услуг
- `services/admin.py` - Админ-панель для Service

**Модель Service:**
- organization (FK → Organization)
- title
- description
- price
- duration (в минутах)
- is_active
- created_at

#### 4. Bookings (Бронирования)
**Файлы:**
- `bookings/models.py` - Модель Booking
- `bookings/serializers.py` - BookingSerializer
- `bookings/views.py` - BookingViewSet
- `bookings/urls.py` - API endpoints для бронирований
- `bookings/admin.py` - Админ-панель для Booking

**Модель Booking:**
- user (FK → User)
- service (FK → Service)
- status (NEW / CONFIRMED / CANCELLED / DONE)
- scheduled_at
- created_at

### API Endpoints
```
/api/users/          - GET, POST
/api/users/{id}/     - GET, PUT, PATCH, DELETE

/api/organizations/      - GET, POST
/api/organizations/{id}/ - GET, PUT, PATCH, DELETE

/api/services/       - GET, POST
/api/services/{id}/  - GET, PUT, PATCH, DELETE

/api/bookings/       - GET, POST
/api/bookings/{id}/  - GET, PUT, PATCH, DELETE
```

### Конфигурация
- `pioneer_backend/settings.py` - Добавлен AUTH_USER_MODEL = 'users.User'
- `pioneer_backend/urls.py` - Подключены все API endpoints
- `README.md` - Документация проекта
- `create_db.sql` - SQL скрипт для создания БД

### ER-модель
```
User
├─ owns → Organization (1:N)
├─ books → Booking (1:N)

Organization
├─ has → Service (1:N)

Service
├─ booked in → Booking (1:N)
```

### Выполненные шаги
1. ✅ Создана база данных PostgreSQL: `pioneer`
2. ✅ Применены миграции: `python manage.py makemigrations && python manage.py migrate`
3. ✅ Создан суперпользователь: admin@example.com
4. ✅ Сервер запущен: http://127.0.0.1:8000/

### Доступные endpoints
- http://127.0.0.1:8000/admin/ - Админ-панель Django
- http://127.0.0.1:8000/api/users/ - API пользователей
- http://127.0.0.1:8000/api/organizations/ - API организаций
- http://127.0.0.1:8000/api/services/ - API услуг
- http://127.0.0.1:8000/api/bookings/ - API бронирований

### Решенные проблемы
- Исправлена ошибка кодировки UTF-8 в подключении к PostgreSQL
- Изменен DB_HOST с localhost на 127.0.0.1
- Установлен пароль admin123 для пользователя postgres

---

## Для коммита в Git:

```bash
git add .
git commit -m "feat: initial project setup with domain-driven architecture

- Configure PostgreSQL with environment variables
- Implement custom User model with email authentication
- Create domain apps: users, organizations, services, bookings
- Setup REST API endpoints for all domains
- Add admin panel configuration for all models
- Configure CORS and DRF settings"
```


---

## 2026-02-27 - Добавлена авторизация и восстановление доступа через Email

### Email-коды подтверждения
- ✅ Реализована отправка 4-значных кодов на email
- ✅ Коды хранятся в Django cache (TTL: 5 минут)
- ✅ Тестовый код для разработки: `4444`
- ✅ В dev режиме письма выводятся в консоль (console backend)
- ✅ Для продакшена настраивается SMTP через .env

### Новые компоненты

#### EmailVerificationService (`users/email_service.py`)
- Генерация криптографически безопасных кодов
- Отправка HTML-писем через SMTP
- Работа с Django cache для хранения кодов
- Два типа кодов: авторизация и восстановление доступа
- Автоматическое удаление кодов после использования

#### Email Auth Views (`users/email_auth_views.py`)
- `send_email_auth_code` - отправка кода авторизации
- `verify_email_auth_code` - проверка кода и вход в систему
- `send_email_recovery_code` - отправка кода восстановления
- `verify_email_recovery_code` - проверка кода восстановления и вход
- Валидация email
- Создание пользователей и сессий
- Генерация JWT токенов

### Обновленные модели

#### User
- Добавлено поле `email` (unique, nullable, indexed)
- Email используется для авторизации и восстановления доступа
- Совместимость с существующей phone-авторизацией

### API Endpoints

**Авторизация через Email:**
- `POST /api/users/auth/email/send-code/` - отправить код авторизации
- `POST /api/users/auth/email/verify-code/` - проверить код и войти

**Восстановление доступа:**
- `POST /api/users/auth/email/recovery/send-code/` - отправить код восстановления
- `POST /api/users/auth/email/recovery/verify-code/` - проверить код и войти

### Настройки

**Email (settings.py):**
```python
# В режиме разработки письма выводятся в консоль
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # Настройки SMTP из .env
```

**Cache (settings.py):**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5 минут
    }
}
```

### Безопасность
- Криптографически безопасная генерация кодов (secrets.randbelow)
- Одноразовые коды (удаляются после использования)
- Ограничение времени жизни (5 минут)
- Деактивация старых сессий при входе
- Не раскрывается информация о существовании пользователя при восстановлении

### Документация
- ✅ `EMAIL_AUTH_DOCUMENTATION.md` - полная документация API
- ✅ `test_email_service.py` - интерактивный тестовый скрипт

### Зависимости
- Добавлен `djangorestframework-simplejwt==5.5.1`
- Добавлен `pyjwt==2.11.0`

### Миграции
- `users/migrations/0002_user_email_user_users_user_email_6f2530_idx.py`
  - Добавлено поле email
  - Создан индекс на email

### Тестирование
```bash
# Запуск интерактивного теста
python test_email_service.py

# Тест через curl
curl -X POST http://localhost:8000/api/users/auth/email/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "privacy_policy_accepted": true}'
```

### Для коммита в Git:
```bash
git add .
git commit -m "feat: add email authentication and account recovery

- Implement 4-digit email verification codes (TTL: 5 minutes)
- Add EmailVerificationService with Django cache storage
- Create email auth endpoints (send/verify code)
- Create recovery endpoints (send/verify recovery code)
- Add email field to User model with unique constraint
- Configure email backend (console in dev, SMTP in prod)
- Add HTML email templates with Pioneer Study branding
- Implement JWT token generation on successful auth
- Add session management (one active session per device)
- Create comprehensive API documentation
- Add interactive test script for email service
- Test code for development: 4444"
```
