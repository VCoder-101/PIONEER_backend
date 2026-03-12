# Схема базы данных PIONEER Backend

Эта схема описывает фактические модели из текущего кода Django apps `users`, `cars`, `organizations`, `services`, `bookings`.

## Общие замечания

- `User.id` и `UserSession.id` — `UUIDField`.
- Для остальных моделей используется стандартный Django `BigAutoField`.
- `User` наследуется от `AbstractBaseUser` и `PermissionsMixin`, поэтому в физической таблице есть стандартные django-auth поля вроде `password`, `last_login`, `is_superuser` и permission relations.
- Публичная авторизация по паролю в проекте не используется: `create_user()` выставляет unusable password, а пользовательский auth flow работает через email-коды.
- Поле `phone` удалено из модели `User`. Аутентификация строится вокруг `email`.

## Модели

### `users.User`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | UUID PK | да | идентификатор пользователя |
| `email` | `EmailField(unique=True, db_index=True)` | да | основной логин |
| `name` | `CharField(150, null=True, blank=True)` | нет | имя пользователя |
| `role` | `CharField` | да | `ADMIN`, `CLIENT` |
| `is_active` | `BooleanField(db_index=True)` | да | активность учётной записи |
| `is_staff` | `BooleanField` | да | доступ в staff/admin контур |
| `privacy_policy_accepted_at` | `DateTimeField(null=True, blank=True)` | нет | время принятия privacy policy |
| `current_device_id` | `CharField(255, null=True, blank=True)` | нет | текущее устройство |
| `current_session_id` | `UUIDField(null=True, blank=True)` | нет | текущая активная серверная сессия |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | создание записи |
| `updated_at` | `DateTimeField(auto_now=True)` | да | последнее обновление |
| `last_login_at` | `DateTimeField(null=True, blank=True)` | нет | последняя авторизация через email-код |

Индексы из модели:

- `email`
- `(role, is_active)`
- `-created_at`
- `current_session_id`

### `users.UserSession`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | UUID PK | да | идентификатор сессии |
| `user` | FK -> `users.User` | да | пользователь |
| `device_id` | `CharField(255, db_index=True)` | да | идентификатор устройства |
| `ip_address` | `GenericIPAddressField(null=True, blank=True)` | нет | IP клиента |
| `user_agent` | `TextField(blank=True)` | нет | User-Agent |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | начало сессии |
| `expires_at` | `DateTimeField(db_index=True)` | да | срок действия |
| `is_active` | `BooleanField(db_index=True)` | да | признак активной сессии |

Индексы из модели:

- `(user, is_active)`
- `device_id`
- `(expires_at, is_active)`

### `cars.Car`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | UUID PK | да | идентификатор автомобиля |
| `user` | FK -> `users.User` | да | владелец |
| `brand` | `CharField(100)` | да | марка автомобиля, например Toyota, BMW |
| `license_plate` | `CharField(20, unique=True, db_index=True)` | да | госномер, уникальный в системе |
| `wheel_diameter` | `PositiveIntegerField` | да | диаметр диска в дюймах (10–30) |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | дата создания |
| `updated_at` | `DateTimeField(auto_now=True)` | да | дата обновления |

Индексы из модели:

- `(user, -created_at)`
- `license_plate`

### `organizations.City`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор города |
| `name` | `CharField(100, unique=True, db_index=True)` | да | название города |
| `region` | `CharField(100, blank=True)` | нет | регион |
| `country` | `CharField(100, default="Россия")` | да | страна |
| `is_active` | `BooleanField` | да | активность города |
| `created_at` | `DateTimeField(auto_now_add=True)` | да | дата создания |

Индексы из модели:

- `name`
- `is_active`

### `organizations.Organization`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор организации |
| `name` | `CharField(255, db_index=True)` | да | название |
| `owner` | FK -> `users.User` | да | владелец с ролью `ORGANIZATION` или `ADMIN` |
| `city` | FK -> `organizations.City` (`SET_NULL`) | нет | город |
| `address` | `CharField(500, blank=True)` | нет | адрес |
| `phone` | `CharField(20, blank=True)` | нет | телефон организации |
| `email` | `EmailField(blank=True)` | нет | контактный email |
| `description` | `TextField(blank=True)` | нет | описание |
| `is_active` | `BooleanField` | да | активность организации |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | дата создания |

Индексы из модели:

- `(owner, is_active)`
- `(city, is_active)`
- `-created_at`

### `services.Service`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор услуги |
| `organization` | FK -> `organizations.Organization` | да | организация-владелец услуги |
| `title` | `CharField(255, db_index=True)` | да | название |
| `description` | `TextField(blank=True)` | нет | описание |
| `price` | `DecimalField(10, 2, db_index=True)` | да | базовая цена |
| `duration` | `IntegerField` | да | длительность в минутах |
| `is_active` | `BooleanField(db_index=True)` | да | активность услуги |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | дата создания |

Индексы из модели:

- `(organization, is_active)`
- `(is_active, price)`
- `-created_at`

### `services.ServiceItem`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор элемента услуги |
| `service` | FK -> `services.Service` | да | родительская услуга |
| `name` | `CharField(255)` | да | название элемента |
| `description` | `TextField(blank=True)` | нет | описание |
| `price` | `DecimalField(10, 2)` | да | цена элемента |
| `is_required` | `BooleanField(default=False)` | да | обязательный ли элемент |
| `is_active` | `BooleanField(default=True)` | да | активность элемента |
| `order` | `IntegerField(default=0)` | да | порядок сортировки |
| `created_at` | `DateTimeField(auto_now_add=True)` | да | дата создания |

Индексы из модели:

- `(service, is_active)`
- `order`

### `bookings.Booking`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор бронирования |
| `user` | FK -> `users.User` | да | клиент |
| `service` | FK -> `services.Service` | да | выбранная услуга |
| `status` | `CharField` | да | `NEW`, `CONFIRMED`, `CANCELLED`, `DONE` |
| `scheduled_at` | `DateTimeField(db_index=True)` | да | дата и время записи |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | да | дата создания |
| `updated_at` | `DateTimeField(auto_now=True)` | да | дата обновления |

Индексы из модели:

- `(user, status)`
- `(service, status)`
- `(status, scheduled_at)`
- `-created_at`

### `bookings.BookingItem`

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | BigAuto PK | да | идентификатор элемента бронирования |
| `booking` | FK -> `bookings.Booking` | да | бронирование |
| `service_item` | FK -> `services.ServiceItem` | да | выбранный элемент услуги |
| `quantity` | `PositiveIntegerField(default=1)` | да | количество |
| `price` | `DecimalField(10, 2)` | да | цена на момент бронирования |

Индексы из модели:

- `booking`

## Связи между сущностями

- один `User` -> много `UserSession`
- один `User` -> много `Car`
- один `User` -> много `Organization` через `owner`
- один `User` -> много `Booking`
- один `City` -> много `Organization`
- одна `Organization` -> много `Service`
- одна `Service` -> много `ServiceItem`
- одна `Service` -> много `Booking`
- один `Booking` -> много `BookingItem`
- один `ServiceItem` -> много `BookingItem`

## Упрощённая ER-схема

```text
User (UUID)
  ├─< UserSession (UUID)
  ├─< Car (UUID)
  ├─< Organization
  └─< Booking

City
  └─< Organization

Organization
  └─< Service

Service
  ├─< ServiceItem
  └─< Booking

Booking
  └─< BookingItem >─ ServiceItem
```

## Что важно не перепутать

- поля `phone` в `User` нет: аутентификация строится вокруг `email`; `phone` есть только у `Organization` как контактный номер организации.
- отдельной доменной модели для слотов, доступности услуги, параметров услуги и заявок на подключение организации в коде пока нет.
- `BookingItem` существует в БД, но публичный booking API пока не даёт полноценного nested create/update сценария для этих записей.
- `Organization.city` и `Organization.address` пока не обязательны на уровне модели, хотя product-level требования в будущем могут стать строже.

## Связанные документы

- [README.md](README.md)
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
