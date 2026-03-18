# Changelog - PIONEER Backend

## [Unreleased] - 2026-03-18

### 🔒 Security & Authentication

#### БАГ-001: Инвалидация access токенов
- **Fixed:** Старые access токены теперь инвалидируются при обновлении
- **Added:** `session_id` в JWT payload для отслеживания активных сессий
- **Added:** `SessionAwareJWTAuthentication` для проверки активности сессии
- **Breaking:** `/api/token/refresh/` теперь требует обязательное поле `device_id`
- **Files:** `users/authentication.py`, `users/token_views.py`, `users/email_auth_views.py`, `users/jwt_views.py`

#### БАГ-004: Rate Limiting
- **Fixed:** Повторная отправка кода теперь возвращает 429 вместо 500
- **Files:** `users/email_auth_views.py`

### 🏢 Organizations

#### БАГ-002: Создание организации
- **Fixed:** CLIENT теперь может создавать организации
- **Fixed:** Поля `organizationStatus` и `owner` теперь read-only
- **Files:** `organizations/permissions.py`, `organizations/serializers.py`

#### БАГ-006: Данные организации
- **Added:** Поля `countServices` и `summaryPrice` в ответ API
- **Files:** `organizations/models.py`, `organizations/serializers.py`

#### БАГ-009: Уникальность организаций
- **Added:** Проверка уникальности названия организации (case-insensitive)
- **Files:** `organizations/serializers.py`

### 🛠️ Services

#### БАГ-008: Редактирование услуг
- **Fixed:** Владельцы организаций могут редактировать свои услуги
- **Files:** `services/permissions.py`

#### БАГ-010: Создание услуг
- **Fixed:** Услуги можно создавать только для одобренных организаций
- **Added:** Проверка статуса организации (approved) при создании услуги
- **Files:** `services/permissions.py`, `services/views.py`

### 📅 Bookings

#### БАГ-003: Создание бронирования
- **Fixed:** Поле `user` устанавливается автоматически
- **Added:** Поддержка camelCase и snake_case форматов
- **Changed:** Поля `dateTime` и `carModel` теперь опциональны
- **Files:** `bookings/serializers.py`

#### БАГ-005: Статус бронирования
- **Fixed:** Поле `status` теперь всегда возвращается в ответе
- **Files:** `bookings/serializers.py`

#### БАГ-011: Календарь бронирований
- **Added:** Поле `bookingStatus` (active/archived) в календарь
- **Logic:** NEW, CONFIRMED → active; CANCELLED, DONE → archived
- **Files:** `bookings/serializers.py`

#### Новые endpoints для управления бронированиями
- **Added:** `POST /api/bookings/{id}/confirm/` - подтверждение (NEW → CONFIRMED)
- **Added:** `POST /api/bookings/{id}/complete/` - завершение (CONFIRMED → DONE)
- **Access:** Организация (владелец), Администратор
- **Files:** `bookings/views.py`

### 🔧 Technical

#### БАГ-007: URL без trailing slash
- **Fixed:** Настроен `APPEND_SLASH=False` для корректной обработки
- **Files:** `pioneer_backend/settings.py`

### 📚 Documentation

- **Updated:** `API_DOCUMENTATION.md` - обновлена с учетом всех исправлений
- **Added:** `API_CHANGES_SUMMARY.md` - сводка изменений API
- **Added:** `BUGS_FIXED_SUMMARY.md` - сводка исправленных багов
- **Added:** `BOOKING_CONFIRM_COMPLETE_IMPLEMENTATION.md` - документация новых endpoints
- **Added:** `BUG_001_FIX.md` - `BUG_011_FIX.md` - детальная документация по каждому багу

### 🧪 Tests

- **Added:** `test_bug_010_service_create.py` - тест создания услуг
- **Added:** `test_bug_011_calendar_status.py` - тест статуса в календаре
- **Added:** `test_bug_011_calendar_status_full.py` - полный тест статусов
- **Added:** `test_booking_status_transitions.py` - тест переходов статусов
- **Added:** `create_admin.py` - утилита для создания администратора

### 🔄 Breaking Changes

1. **БАГ-001:** `/api/token/refresh/` теперь требует `device_id`
   ```json
   {
     "refresh": "eyJ...",
     "device_id": "unique-device-identifier"  // ОБЯЗАТЕЛЬНО
   }
   ```

### ⚠️ Deprecations

Нет устаревших функций в этом релизе.

### 📊 Statistics

- **Исправлено багов:** 11
- **Новых endpoints:** 2
- **Измененных файлов:** 15+
- **Созданных тестов:** 5
- **Документации:** 15+ файлов

### 🎯 Migration Guide

#### 1. Обновите refresh token запросы
```javascript
// Было
fetch('/api/token/refresh/', {
  body: JSON.stringify({ refresh: refreshToken })
})

// Стало
fetch('/api/token/refresh/', {
  body: JSON.stringify({ 
    refresh: refreshToken,
    device_id: getDeviceId()  // Добавьте device_id
  })
})
```

#### 2. Обновите создание бронирований
```javascript
// Было
{
  user: userId,  // Удалите это поле
  service: serviceId,
  scheduled_at: "2026-03-20T10:00:00Z"
}

// Стало
{
  service: serviceId,
  scheduled_at: "2026-03-20T10:00:00Z"
  // user устанавливается автоматически
}
```

#### 3. Используйте bookingStatus для фильтрации
```javascript
// Фильтрация активных бронирований
bookings.filter(b => b.bookingStatus === 'active')

// Фильтрация архивных бронирований
bookings.filter(b => b.bookingStatus === 'archived')
```

#### 4. Используйте новые endpoints для управления бронированиями
```javascript
// Подтверждение
POST /api/bookings/{id}/confirm/

// Завершение
POST /api/bookings/{id}/complete/

// Отмена
POST /api/bookings/{id}/cancel/
```

### 🔗 Links

- [API Documentation](./API_DOCUMENTATION.md)
- [API Changes Summary](./API_CHANGES_SUMMARY.md)
- [Bugs Fixed Summary](./BUGS_FIXED_SUMMARY.md)
- [Booking Confirm/Complete Implementation](./BOOKING_CONFIRM_COMPLETE_IMPLEMENTATION.md)

---

## Previous Releases

История предыдущих релизов будет добавлена позже.
