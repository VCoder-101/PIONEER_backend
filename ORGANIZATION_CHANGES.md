# Изменения в модели Organization

## Выполненные задачи

### 1. Убрана роль ORGANIZATION из модели User
- Удалена роль 'ORGANIZATION' из ROLE_CHOICES
- Создана миграция для обновления существующих данных

### 2. Добавлены новые поля в модель Organization

#### Статус заявки
- `organization_status` - статус заявки (pending/approved/rejected)
- `organization_date_approved` - дата одобрения (автоматически устанавливается)

#### Государственные данные
- `org_inn` - ИНН (до 12 символов)
- `org_ogrn` - ОГРН (до 15 символов) 
- `org_kpp` - КПП (до 9 символов)

#### Тип организации и дополнительные поля
- `organization_type` - тип организации (wash/tire)
- `short_name` - короткое название
- `wheel_diameters` - массив диаметров дисков (JSON поле)

#### Статистика
- `count_services` - количество услуг (только для чтения)
- `summary_price` - итоговая стоимость (только для чтения)

### 3. Обновлен API сериализатор
Приведен к требуемому формату с полями:
- `shortName` (вместо short_name)
- `organizationStatus` (вместо organization_status)
- `organizationDateApproved` (формат DD/MM/YYYY)
- `organizationType` (вместо organization_type)
- `orgOgrn`, `orgInn`, `orgKpp`
- `wheelDiameters` (для шиномонтажа)
- `countServices`, `summaryPrice`

### 4. Обновлена админка
- Добавлены новые поля в список отображения
- Настроены фильтры по статусу и типу организации
- Организованы fieldsets для удобного редактирования
- Поля статистики доступны только для чтения

### 5. Автоматическая установка даты одобрения
При изменении статуса на 'approved' автоматически устанавливается дата одобрения.

## Пример API ответа

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "TEST ORG",
      "shortName": "TST",
      "organizationStatus": "approved",
      "organizationDateApproved": "11/03/2026",
      "owner": "43ec9bfe-8ba3-4a3e-8081-c9eb177849a4",
      "owner_email": "test@example.com",
      "city": 1,
      "address": "Ново-Садовая улица, 200",
      "phone": "+79033093257",
      "email": "m.romanov.biz@gmail.com",
      "description": "sfsafsdg",
      "is_active": true,
      "created_at": "2026-03-11T09:47:35.756317Z",
      "organizationType": "wash",
      "orgOgrn": "1234543521234",
      "orgInn": "123123123534",
      "orgKpp": "777743621",
      "wheelDiameters": [13, 14, 15, 16, 17, 18],
      "countServices": 12,
      "summaryPrice": "12000.00"
    }
  ]
}
```

## Миграции
- `organizations/migrations/0004_*` - добавление новых полей
- `users/migrations/0005_*` - удаление роли ORGANIZATION

---

# Изменения в модели Service

## Выполненные задачи

### 1. Добавлено поле status для скрытия услуг
- `status` - статус услуги ('active'/'ghost')
- По умолчанию все услуги имеют статус 'active'
- Услуги со статусом 'ghost' скрыты от клиентов, но видны владельцам организаций

### 2. Обновлена логика видимости услуг
- **Клиенты**: видят только услуги с `is_active=True` и `status='active'`
- **Владельцы организаций**: видят все свои услуги (включая 'ghost')
- **Администраторы**: видят все услуги

### 3. Добавлена возможность редактирования услуг
- Владельцы организаций могут редактировать только свои услуги
- Администраторы могут редактировать любые услуги
- Добавлен метод `perform_update` в `ServiceViewSet`

### 4. Обновлен API
- Добавлено поле `status` в сериализатор
- Добавлен фильтр по полю `status`
- Обновлена логика в `ServiceItemViewSet` для учета статуса услуги

### 5. Обновлена админка
- Добавлено поле `status` в список отображения
- Добавлен фильтр по статусу

## Пример использования

### Создание скрытой услуги
```json
{
  "organization": 1,
  "title": "VIP мойка",
  "description": "Премиум услуга",
  "price": "1500.00",
  "duration": 60,
  "status": "ghost"
}
```

### Пример API ответа
```json
{
  "id": 1,
  "organization": 1,
  "organization_name": "TEST ORG",
  "title": "Мойка автомобиля",
  "description": "Полная мойка автомобиля",
  "price": "500.00",
  "duration": 30,
  "status": "active",
  "is_active": true,
  "items": [],
  "created_at": "2026-03-11T09:55:51.792940Z"
}
```

## Миграции
- `services/migrations/0003_*` - добавление поля status и индекса
---

# Исправление проблемы с отображением бронирований

## Проблема
После удаления роли 'ORGANIZATION' из модели User, владельцы организаций не могли видеть бронирования на свои услуги, так как логика в BookingViewSet была привязана к этой роли.

## Решение

### 1. Обновлена логика в BookingViewSet.get_queryset()
Вместо проверки роли 'ORGANIZATION' теперь проверяется, является ли пользователь владельцем организации:

```python
def get_queryset(self):
    user = self.request.user
    if user.role == 'ADMIN':
        return Booking.objects.all()
    else:
        # Проверяем, является ли пользователь владельцем организации
        user_organizations = user.organizations.all()
        if user_organizations.exists():
            # Пользователь владеет организациями - показываем брони на его услуги + свои брони
            return Booking.objects.filter(
                models.Q(service__organization__owner=user) | 
                models.Q(user=user)
            ).distinct()
        else:
            # Обычный клиент - видит только свои бронирования
            return Booking.objects.filter(user=user)
```

### 2. Обновлены permissions в IsBookingOwnerOrServiceOwner
Убрана привязка к роли 'ORGANIZATION', теперь проверяется прямое владение организацией:

```python
def has_object_permission(self, request, view, obj):
    # Админ может всё
    if request.user.role == 'ADMIN':
        return True
    
    # Клиент может управлять своими бронированиями
    if obj.user == request.user:
        return True
    
    # Владелец организации может видеть брони на услуги своей организации
    if obj.service.organization.owner == request.user:
        return True
    
    return False
```

## Результат
Теперь владельцы организаций (независимо от роли) могут:
- Видеть все бронирования на услуги своих организаций
- Видеть свои собственные бронирования как клиенты
- Управлять бронированиями через API

## Пример API ответа для владельца организации
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": "fee53bf2-cf35-433a-b062-65336315e78a",
      "user_email": "luk_2004ru@mail.ru",
      "service": 2,
      "service_title": "VIP мойка",
      "status": "NEW",
      "scheduled_at": "2026-03-12T09:59:54.747484Z",
      "items": [],
      "created_at": "2026-03-11T09:59:54.747484Z",
      "updated_at": "2026-03-11T09:59:54.748484Z"
    }
  ]
}
```
---

# Добавление полей модель авто и диаметр диска в бронирования

## Выполненные задачи

### 1. Добавлены новые поля в модель Booking
- `car_model` - модель автомобиля (CharField, до 100 символов)
- `wheel_diameter` - диаметр диска (IntegerField, может быть null)

### 2. Обновлен сериализатор BookingSerializer
Добавлены поля в новом формате для соответствия требуемому API:
- `customerName` (source='user.name') - имя клиента
- `dateTime` (source='scheduled_at', format='%d/%m/%Y %H:%M') - дата и время
- `carModel` (source='car_model') - модель автомобиля  
- `serviceMethod` (source='service.title') - название услуги
- `duration` (source='service.duration') - длительность услуги
- `price` (source='service.price') - цена услуги
- `wheelDiameter` (source='wheel_diameter') - диаметр диска

### 3. Создан дополнительный InvoiceSerializer
Упрощенный сериализатор специально для формата invoices с полями:
`id`, `customerName`, `dateTime`, `carModel`, `serviceMethod`, `duration`, `price`

### 4. Обновлена админка
- Добавлены новые поля в отображение и фильтры
- Организованы fieldsets для удобного редактирования
- Добавлен поиск по модели автомобиля

## Пример API ответа в новом формате

### Формат invoices (упрощенный)
```javascript
const invoices = [
  {
    id: 2,
    customerName: "Иван Петров",
    dateTime: "12/03/2026 20:33",
    carModel: "Lada Vesta",
    serviceMethod: "VIP мойка",
    duration: "60",
    price: 1500.0
  },
  {
    id: 3,
    customerName: "Иван Петров", 
    dateTime: "14/03/2026 00:03",
    carModel: "Lada Granta",
    serviceMethod: "VIP мойка",
    duration: "60",
    price: 1500.0
  }
]
```

### Полный API ответ
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "customerName": "Иван Петров",
      "dateTime": "12/03/2026 20:33",
      "carModel": "Lada Vesta",
      "serviceMethod": "VIP мойка",
      "duration": "60",
      "price": "1500.00",
      "wheelDiameter": 16,
      "user": "45fe4874-73b3-4af8-88da-e27dec15961b",
      "user_email": "client_with_name@test.com",
      "service": 2,
      "service_title": "VIP мойка",
      "status": "CONFIRMED",
      "scheduled_at": "2026-03-12T20:33:45.663353Z",
      "car_model": "Lada Vesta",
      "wheel_diameter": 16,
      "items": [],
      "created_at": "2026-03-11T10:03:45.665355Z",
      "updated_at": "2026-03-11T10:03:45.665355Z"
    }
  ]
}
```

## Миграции
- `bookings/migrations/0005_*` - добавление полей car_model и wheel_diameter
---

# Система заявок на подключение к агрегатору

## Статус реализации: ✅ ВЫПОЛНЕНО

### 1. ✅ Таблица с заявками на подключение
**Реализовано в модели Organization:**
- `organization_status` - статус заявки (pending/approved/rejected)
- `organization_date_approved` - дата одобрения
- Автоматическая установка даты при одобрении
- Сброс даты при отклонении

### 2. ✅ Логика записи и отображения данных
**API endpoints:**
- `GET /api/organizations/` - просмотр всех организаций (с фильтрацией по статусу)
- `POST /api/organizations/` - создание новой заявки (автоматически статус 'pending')
- Фильтрация по `organization_status`, `organization_type`, `city`, `is_active`

**Права доступа:**
- **Администраторы**: видят все организации и заявки
- **Владельцы организаций**: видят только свои организации
- **Клиенты**: видят только одобренные активные организации

### 3. ✅ Логика аппрува и деаппрува
**Специальные endpoints для администраторов:**

#### `POST /api/organizations/{id}/approve/`
Одобрить заявку организации:
```json
{
  "message": "Заявка одобрена",
  "organization": { ... }
}
```

#### `POST /api/organizations/{id}/reject/`
Отклонить заявку организации:
```json
{
  "message": "Заявка отклонена", 
  "organization": { ... }
}
```

#### `GET /api/organizations/pending/`
Получить все заявки на рассмотрении:
```json
{
  "count": 1,
  "results": [ ... ]
}
```

### 4. ✅ Безопасность
- Только администраторы могут одобрять/отклонять заявки
- Автоматическая проверка прав доступа
- Возврат ошибки 403 для неавторизованных действий

### 5. ✅ Админка
- Отображение статуса заявки в списке организаций
- Фильтрация по статусу
- Группировка полей по категориям
- Поля даты одобрения и статистики только для чтения

## Пример использования

### Создание заявки
```bash
POST /api/organizations/
{
  "name": "Моя автомойка",
  "short_name": "МА", 
  "organization_type": "wash",
  "city": 1,
  "address": "ул. Примерная, 123",
  "phone": "+79999999999",
  "email": "info@mycarwash.ru",
  "org_inn": "123456789012",
  "org_ogrn": "123456789012345",
  "org_kpp": "123456789"
}
```
Автоматически устанавливается `organization_status: "pending"`

### Одобрение администратором
```bash
POST /api/organizations/1/approve/
```
Результат:
- `organization_status` → "approved"
- `organization_date_approved` → текущая дата/время

### Просмотр заявок на рассмотрении
```bash
GET /api/organizations/pending/
```

### Фильтрация по статусу
```bash
GET /api/organizations/?organization_status=pending
GET /api/organizations/?organization_status=approved
GET /api/organizations/?organization_status=rejected
```

## Статистика по статусам
- **На рассмотрении**: организации ожидают решения администратора
- **Одобрена**: организации могут работать в системе
- **Отклонена**: заявки отклонены администратором