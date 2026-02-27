# Схема базы данных Pioneer Backend

## ER-диаграмма (текстовая)

```
┌─────────────────────┐
│       User          │
│─────────────────────│
│ id (PK)            │◄────┐
│ email (unique) ⚡   │     │
│ password           │     │
│ role ⚡            │     │
│ is_active ⚡       │     │
│ created_at ⚡      │     │
│ last_login         │     │
└─────────────────────┘     │
         │                  │
         │ 1:N              │ 1:N
         ▼                  │
┌─────────────────────┐     │
│   UserSession       │     │
│─────────────────────│     │
│ id (PK)            │     │
│ user_id (FK) ⚡    │─────┘
│ session_key ⚡     │
│ ip_address         │
│ user_agent         │
│ created_at ⚡      │
│ expires_at ⚡      │
│ is_active ⚡       │
└─────────────────────┘


┌─────────────────────┐
│       City          │
│─────────────────────│
│ id (PK)            │◄────┐
│ name (unique) ⚡    │     │
│ region             │     │
│ country            │     │
│ is_active ⚡       │     │
│ created_at         │     │
└─────────────────────┘     │
                            │ 1:N
┌─────────────────────┐     │
│   Organization      │     │
│─────────────────────│     │
│ id (PK)            │     │
│ name ⚡            │     │
│ owner_id (FK) ⚡   │─────┼──► User
│ city_id (FK) ⚡    │─────┘
│ address            │
│ phone              │
│ email              │
│ description        │
│ is_active ⚡       │
│ created_at ⚡      │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│      Service        │
│─────────────────────│
│ id (PK)            │◄────┐
│ organization_id ⚡  │     │
│ title ⚡           │     │
│ description        │     │
│ price ⚡           │     │
│ duration           │     │
│ is_active ⚡       │     │
│ created_at ⚡      │     │
└─────────────────────┘     │
         │                  │
         │ 1:N              │ 1:N
         ▼                  │
┌─────────────────────┐     │
│   ServiceItem       │     │
│─────────────────────│     │
│ id (PK)            │     │
│ service_id (FK) ⚡  │─────┘
│ name               │
│ description        │
│ price              │
│ is_required        │
│ is_active ⚡       │
│ order ⚡           │
│ created_at         │
└─────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│   BookingItem       │
│─────────────────────│
│ id (PK)            │
│ booking_id (FK) ⚡  │─────┐
│ service_item_id ⚡  │     │
│ quantity           │     │
│ price              │     │
└─────────────────────┘     │
                            │
┌─────────────────────┐     │
│      Booking        │     │
│─────────────────────│     │
│ id (PK)            │◄────┘
│ user_id (FK) ⚡    │─────► User
│ service_id (FK) ⚡  │─────► Service
│ status ⚡          │
│ scheduled_at ⚡    │
│ created_at ⚡      │
│ updated_at         │
└─────────────────────┘
```

⚡ - Поле с индексом

---

## Связи между таблицами

### User (Пользователи)
- **1:N** → Organization (владелец организаций)
- **1:N** → Booking (клиент создает бронирования)
- **1:N** → UserSession (сессии пользователя)

### City (Города)
- **1:N** → Organization (город организации)

### Organization (Организации)
- **N:1** → User (владелец)
- **N:1** → City (город)
- **1:N** → Service (услуги организации)

### Service (Услуги)
- **N:1** → Organization (организация)
- **1:N** → ServiceItem (элементы услуги)
- **1:N** → Booking (бронирования услуги)

### ServiceItem (Элементы услуг)
- **N:1** → Service (услуга)
- **1:N** → BookingItem (выбранные элементы)

### Booking (Бронирования)
- **N:1** → User (клиент)
- **N:1** → Service (услуга)
- **1:N** → BookingItem (элементы бронирования)

### BookingItem (Элементы бронирования)
- **N:1** → Booking (бронирование)
- **N:1** → ServiceItem (элемент услуги)

---

## Индексы для оптимизации

### Одиночные индексы (db_index=True)

**User:**
- email (unique)
- role
- is_active
- created_at

**UserSession:**
- user_id (FK)
- session_key (unique)
- is_active
- created_at
- expires_at

**City:**
- name (unique)
- is_active

**Organization:**
- name
- owner_id (FK)
- city_id (FK)
- is_active
- created_at

**Service:**
- organization_id (FK)
- title
- price
- is_active
- created_at

**ServiceItem:**
- service_id (FK)
- is_active
- order

**Booking:**
- user_id (FK)
- service_id (FK)
- status
- scheduled_at
- created_at

**BookingItem:**
- booking_id (FK)
- service_item_id (FK)

### Составные индексы (Meta.indexes)

**User:**
1. (email)
2. (role, is_active)
3. (-created_at)

**UserSession:**
1. (user, is_active)
2. (session_key)
3. (expires_at, is_active)

**City:**
1. (name)
2. (is_active)

**Organization:**
1. (owner, is_active)
2. (city, is_active)
3. (-created_at)

**Service:**
1. (organization, is_active)
2. (is_active, price)
3. (-created_at)

**ServiceItem:**
1. (service, is_active)
2. (order)

**Booking:**
1. (user, status)
2. (service, status)
3. (status, scheduled_at)
4. (-created_at)

**BookingItem:**
1. (booking)

---

## Типичные запросы и их оптимизация

### 1. Получить активные услуги организации
```sql
SELECT * FROM services_service 
WHERE organization_id = ? AND is_active = true
ORDER BY price;
```
**Индекс:** (organization, is_active) + price

### 2. Получить бронирования клиента
```sql
SELECT * FROM bookings_booking 
WHERE user_id = ? AND status = 'NEW'
ORDER BY scheduled_at;
```
**Индекс:** (user, status) + scheduled_at

### 3. Получить активные сессии пользователя
```sql
SELECT * FROM users_usersession 
WHERE user_id = ? AND is_active = true AND expires_at > NOW();
```
**Индекс:** (user, is_active) + (expires_at, is_active)

### 4. Поиск организаций по городу
```sql
SELECT * FROM organizations_organization 
WHERE city_id = ? AND is_active = true;
```
**Индекс:** (city, is_active)

### 5. Получить элементы услуги
```sql
SELECT * FROM services_serviceitem 
WHERE service_id = ? AND is_active = true
ORDER BY order;
```
**Индекс:** (service, is_active) + order

---

## Статистика

- **Таблиц:** 8
- **Связей (FK):** 11
- **Одиночных индексов:** 30+
- **Составных индексов:** 17
- **Всего индексов:** 47+

---

## Размер данных (примерная оценка)

При 1000 пользователей, 100 организаций, 500 услуг:

| Таблица | Записей | Размер (примерно) |
|---------|---------|-------------------|
| User | 1,000 | ~100 KB |
| UserSession | 2,000 | ~200 KB |
| City | 100 | ~10 KB |
| Organization | 100 | ~50 KB |
| Service | 500 | ~200 KB |
| ServiceItem | 2,000 | ~500 KB |
| Booking | 5,000 | ~500 KB |
| BookingItem | 10,000 | ~800 KB |
| **Итого** | **20,700** | **~2.4 MB** |

*Без учета индексов (индексы добавляют ~30-50% к размеру)*
