# БАГ-002: Исправление создания организации клиентом

## 🐛 Описание проблемы

**ID:** BUG-002 (TC-ORG-06)  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено

### Симптом
Пользователь с ролью CLIENT не может создать заявку на регистрацию организации. При попытке создания получает ошибку "Доступ запрещен".

### Шаги воспроизведения
1. Авторизоваться под клиентом (роль CLIENT)
2. Отправить POST запрос на `/api/organizations/` с валидными данными
3. Получить ошибку 403 Forbidden

**Ожидаемый результат:** Организация создается со статусом `pending`  
**Фактический результат (до исправления):** Ошибка "Доступ запрещен"

---

## ✅ Решение

### Причина бага
В `organizations/permissions.py` класс `IsOrganizationOwner` имел неправильную логику:
- Разрешал создание организаций только пользователям, у которых УЖЕ есть организации
- Клиенты без организаций могли только читать данные
- Это создавало замкнутый круг: чтобы создать организацию, нужно уже иметь организацию

### Исправление
Обновлена логика `has_permission()` в `IsOrganizationOwner`:

**Было:**
```python
# Владельцы организаций могут создавать и читать
if hasattr(request.user, 'organizations') and request.user.organizations.exists():
    return True

# Клиенты могут только читать
if request.method in permissions.SAFE_METHODS:
    return True

return False
```

**Стало:**
```python
# Любой авторизованный пользователь может создать организацию (заявку)
if request.method == 'POST' and view.action == 'create':
    return True

# Владельцы организаций могут управлять своими организациями
if hasattr(request.user, 'organizations') and request.user.organizations.exists():
    return True

# Все авторизованные могут читать
if request.method in permissions.SAFE_METHODS:
    return True

return False
```

---

## 🔒 Логика permissions после исправления

### Создание организации (POST /api/organizations/)
- ✅ **Любой авторизованный пользователь** может создать организацию
- Организация создается со статусом `pending` (на рассмотрении)
- Автоматически устанавливается `owner = request.user`

### Чтение организаций (GET /api/organizations/)
- ✅ **ADMIN** - видит все организации
- ✅ **Владелец организации** - видит свои организации
- ✅ **CLIENT** - видит только активные одобренные организации (`is_active=True`, `organization_status='approved'`)

### Обновление/удаление организации (PUT/PATCH/DELETE)
- ✅ **ADMIN** - может управлять любой организацией
- ✅ **Владелец** - может управлять только своей организацией
- ❌ **Другие пользователи** - не могут изменять чужие организации

### Одобрение/отклонение заявок
- ✅ **Только ADMIN** может одобрять/отклонять заявки
- Эндпоинты: `/api/organizations/{id}/approve/`, `/api/organizations/{id}/reject/`

---

## 📝 Измененные файлы

### `organizations/permissions.py`
Обновлен класс `IsOrganizationOwner`:
- Добавлена проверка `if request.method == 'POST' and view.action == 'create'`
- Теперь любой авторизованный пользователь может создать организацию

### `organizations/serializers.py`
Обновлен класс `OrganizationSerializer`:
- Поле `organizationStatus` помечено как `read_only=True`
- Поле `owner` добавлено в `read_only_fields`
- Эти поля устанавливаются автоматически при создании

---

## 🧪 Тестирование

Создан тестовый скрипт `test_bug_002_organization_create.py`:

```bash
# Терминал 1: Запустить сервер
python manage.py runserver

# Терминал 2: Запустить тест
python test_bug_002_organization_create.py
```

### Тест проверяет:
1. ✅ Авторизация под клиентом (роль CLIENT)
2. ✅ Создание организации с валидными данными
3. ✅ Статус организации установлен в `pending`
4. ✅ Организация видна владельцу

### Ожидаемый результат:
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-002 ИСПРАВЛЕН!
```

---

## 🔄 Поток создания организации

```
1. CLIENT авторизуется
   ↓
2. Отправляет POST /api/organizations/ с данными
   ↓
3. IsOrganizationOwner.has_permission() → True (для create)
   ↓
4. OrganizationViewSet.perform_create() устанавливает owner
   ↓
5. Организация создается со статусом 'pending'
   ↓
6. ADMIN видит заявку в /api/organizations/pending/
   ↓
7. ADMIN одобряет через /api/organizations/{id}/approve/
   ↓
8. Статус меняется на 'approved', устанавливается дата одобрения
   ↓
9. Организация становится видна всем клиентам
```

---

## 📊 Матрица доступа

| Действие | ADMIN | Владелец | CLIENT без орг. | CLIENT с орг. |
|----------|-------|----------|-----------------|---------------|
| Создать организацию | ✅ | ✅ | ✅ | ✅ |
| Просмотр всех организаций | ✅ | ❌ | ❌ | ❌ |
| Просмотр своих организаций | ✅ | ✅ | ❌ | ✅ |
| Просмотр одобренных организаций | ✅ | ✅ | ✅ | ✅ |
| Редактировать свою организацию | ✅ | ✅ | ❌ | ✅ |
| Редактировать чужую организацию | ✅ | ❌ | ❌ | ❌ |
| Одобрить заявку | ✅ | ❌ | ❌ | ❌ |
| Отклонить заявку | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Развертывание

### Миграции
Не требуются - изменения только в логике permissions.

### Обратная совместимость
✅ Полная обратная совместимость - изменения только расширяют права доступа.

---

## ✅ Чеклист

- [x] Обновлен `organizations/permissions.py`
- [x] Обновлен `organizations/serializers.py`
- [x] Создан тест `test_bug_002_organization_create.py`
- [x] Создан прямой тест `test_bug_002_direct.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущены оба теста - ✅ ОБА ПРОЙДЕНЫ
- [ ] Обновлена документация API

---

## 🧪 Ручное тестирование

### 1. Авторизация
```bash
curl -X POST http://127.0.0.1:8000/api/users/auth/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","privacy_policy_accepted":true}'

curl -X POST http://127.0.0.1:8000/api/users/auth/verify-code/ \
  -H "Content-Type: application/json" \
  -d '{"email":"client@example.com","code":"XXXX","device_id":"test","name":"Client","privacy_policy_accepted":true}'
```

### 2. Создание организации
```bash
curl -X POST http://127.0.0.1:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
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
  }'
```

Ожидаемый ответ: **201 Created**
```json
{
  "id": 5,
  "name": "Чистый Кузов",
  "organizationStatus": "pending",
  ...
}
```

---

## 📚 Связанные документы

- API_DOCUMENTATION.md - документация API
- ORGANIZATION_CHANGES.md - история изменений организаций
- organizations/models.py - модель Organization
