# БАГ-009: Добавление API для отмены заявки на регистрацию организации

**ID:** BUG-009  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

Отсутствовал API endpoint для отмены заявки на регистрацию организации владельцем. Пользователь не мог отменить свою заявку со статусом `pending`.

## Решение

Добавлен новый action `cancel` в `OrganizationViewSet`:

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
def cancel(self, request, pk=None):
    """
    Отменить заявку на регистрацию организации (только для владельца).
    Доступно только для заявок со статусом 'pending'.
    """
    organization = self.get_object()
    
    # Проверка прав: только владелец или админ
    if organization.owner != request.user and request.user.role != 'ADMIN':
        return Response(
            {'error': 'У вас нет прав на отмену этой заявки'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Проверка статуса: можно отменить только заявки на рассмотрении
    if organization.organization_status != 'pending':
        return Response(
            {
                'error': f'Нельзя отменить заявку со статусом "{organization.get_organization_status_display()}". '
                        'Отменить можно только заявки на рассмотрении.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Отменяем заявку (меняем статус на rejected)
    old_status = organization.organization_status
    organization.organization_status = 'rejected'
    organization.organization_date_approved = None
    organization.save()
    
    serializer = self.get_serializer(organization)
    
    return Response({
        'message': 'Заявка на регистрацию организации успешно отменена',
        'old_status': old_status,
        'organization': serializer.data
    }, status=status.HTTP_200_OK)
```

## API Endpoint

### POST /api/organizations/{id}/cancel/

Отменяет заявку на регистрацию организации.

**Требования:**
- Пользователь должен быть авторизован
- Пользователь должен быть владельцем организации (или ADMIN)
- Статус организации должен быть `pending`

**Запрос:**
```http
POST /api/organizations/15/cancel/
Authorization: Bearer <access_token>
```

**Успешный ответ (200 OK):**
```json
{
  "message": "Заявка на регистрацию организации успешно отменена",
  "old_status": "pending",
  "organization": {
    "id": 15,
    "name": "My Organization",
    "organizationStatus": "rejected",
    "organizationDateApproved": null,
    ...
  }
}
```

**Ошибки:**

#### 403 Forbidden - Нет прав
```json
{
  "error": "У вас нет прав на отмену этой заявки"
}
```

#### 400 Bad Request - Неверный статус
```json
{
  "error": "Нельзя отменить заявку со статусом \"Одобрена\". Отменить можно только заявки на рассмотрении."
}
```

#### 404 Not Found - Организация не найдена
```json
{
  "detail": "Not found."
}
```

## Логика работы

### Кто может отменить заявку
- ✅ Владелец организации (создатель заявки)
- ✅ Администратор (ADMIN)
- ❌ Другие пользователи

### Какие заявки можно отменить
- ✅ Заявки со статусом `pending` (на рассмотрении)
- ❌ Заявки со статусом `approved` (одобрены)
- ❌ Заявки со статусом `rejected` (уже отклонены)

### Что происходит при отмене
1. Статус организации меняется с `pending` на `rejected`
2. Поле `organization_date_approved` очищается (устанавливается в `null`)
3. Возвращается информация об отмененной организации

## Использование на фронтенде

```javascript
async function cancelOrganizationApplication(organizationId, token) {
  try {
    const response = await fetch(
      `/api/organizations/${organizationId}/cancel/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    if (response.ok) {
      const data = await response.json();
      console.log('Заявка отменена:', data.message);
      return data.organization;
    } else if (response.status === 400) {
      const error = await response.json();
      alert(error.error); // "Нельзя отменить заявку со статусом..."
    } else if (response.status === 403) {
      alert('У вас нет прав на отмену этой заявки');
    }
  } catch (error) {
    console.error('Ошибка отмены заявки:', error);
  }
}

// Использование
cancelOrganizationApplication(15, accessToken);
```

## Тестирование

### Автоматический тест
```bash
python test_bug_009_cancel_organization.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-009 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Создание заявки со статусом `pending`
2. ✅ Отмена заявки владельцем
3. ✅ Статус изменяется на `rejected`
4. ✅ Повторная отмена возвращает ошибку 400
5. ✅ Другой пользователь не может отменить чужую заявку

## Сравнение с другими действиями

| Действие | Кто может | Статус до | Статус после |
|----------|-----------|-----------|--------------|
| `approve` | ADMIN | pending | approved |
| `reject` | ADMIN | pending | rejected |
| `cancel` | Владелец или ADMIN | pending | rejected |

**Разница между `reject` и `cancel`:**
- `reject` - администратор отклоняет заявку
- `cancel` - владелец отменяет свою заявку

## Измененные файлы

- `organizations/views.py` - добавлен метод `cancel()` в `OrganizationViewSet`

## Чеклист

- [x] Добавлен метод `cancel()` в `OrganizationViewSet`
- [x] Создан тест `test_bug_009_cancel_organization.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API
- [ ] Уведомлен frontend о новом endpoint

## Связанные документы

- `organizations/models.py` - модель Organization со статусами
- `organizations/permissions.py` - IsOrganizationOwner
- API_DOCUMENTATION.md - документация API
