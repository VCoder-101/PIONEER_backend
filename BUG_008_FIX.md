# БАГ-008: Исправление уникальности названия организации

**ID:** BUG-008  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

При создании организации через `/api/organizations/` можно было создать несколько организаций с одинаковым названием (`name`) или коротким названием (`shortName`). Это приводило к путанице и дублированию данных.

### Причина
Отсутствовала валидация на уникальность полей `name` и `short_name` в `OrganizationSerializer`.

## Решение

Добавлены методы валидации `validate_name()` и `validate_short_name()` в `OrganizationSerializer`:

```python
def validate_name(self, value):
    """
    Проверяет уникальность названия организации.
    При обновлении исключает текущую организацию из проверки.
    """
    # Нормализуем название (убираем лишние пробелы)
    normalized_name = value.strip()
    
    # Проверяем существование организации с таким названием (регистронезависимо)
    queryset = Organization.objects.filter(name__iexact=normalized_name)
    
    # При обновлении исключаем текущую организацию
    if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)
    
    if queryset.exists():
        raise serializers.ValidationError(
            f"Организация с названием '{normalized_name}' уже существует. "
            "Пожалуйста, выберите другое название."
        )
    
    return normalized_name

def validate_short_name(self, value):
    """
    Проверяет уникальность короткого названия организации (если указано).
    """
    if not value or not value.strip():
        return value
    
    normalized_short_name = value.strip()
    
    # Проверяем существование организации с таким коротким названием
    queryset = Organization.objects.filter(short_name__iexact=normalized_short_name)
    
    # При обновлении исключаем текущую организацию
    if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)
    
    if queryset.exists():
        raise serializers.ValidationError(
            f"Организация с коротким названием '{normalized_short_name}' уже существует. "
            "Пожалуйста, выберите другое название."
        )
    
    return normalized_short_name
```

## Особенности реализации

### 1. Регистронезависимая проверка
Используется `name__iexact` для проверки, что предотвращает создание организаций с названиями, отличающимися только регистром:
- "My Organization" и "my organization" - считаются одинаковыми
- "MY ORGANIZATION" и "My Organization" - считаются одинаковыми

### 2. Нормализация названий
Убираются лишние пробелы в начале и конце названия:
- " My Org " → "My Org"

### 3. Поддержка обновления
При обновлении существующей организации текущая организация исключается из проверки, что позволяет сохранить организацию без изменения названия.

### 4. Опциональное короткое название
Проверка `short_name` выполняется только если поле заполнено.

## Примеры ошибок

### Попытка создать организацию с существующим названием

**Запрос:**
```json
POST /api/organizations/
{
  "name": "Existing Organization",
  "shortName": "EO",
  ...
}
```

**Ответ:** 400 Bad Request
```json
{
  "name": [
    "Организация с названием 'Existing Organization' уже существует. Пожалуйста, выберите другое название."
  ]
}
```

### Попытка создать организацию с существующим коротким названием

**Запрос:**
```json
POST /api/organizations/
{
  "name": "New Organization",
  "shortName": "EO",
  ...
}
```

**Ответ:** 400 Bad Request
```json
{
  "shortName": [
    "Организация с коротким названием 'EO' уже существует. Пожалуйста, выберите другое название."
  ]
}
```

## Тестирование

### Автоматический тест
```bash
python test_bug_008_organization_unique_name.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-008 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Создание первой организации
2. ✅ Попытка создать дубликат (тот же пользователь) - ошибка 400
3. ✅ Попытка создать дубликат (другой пользователь) - ошибка 400
4. ✅ Регистронезависимая проверка (NAME vs name) - ошибка 400
5. ✅ Создание организации с другим названием - успех 201

## Обработка на фронтенде

```javascript
try {
  const response = await fetch('/api/organizations/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      name: formData.orgFullName,
      shortName: formData.orgShortName,
      // ... другие поля
    })
  });

  if (!response.ok) {
    const errors = await response.json();
    
    // Обработка ошибки уникальности названия
    if (errors.name) {
      showError('Название организации', errors.name[0]);
    }
    
    // Обработка ошибки уникальности короткого названия
    if (errors.shortName) {
      showError('Короткое название', errors.shortName[0]);
    }
  }
} catch (error) {
  console.error('Ошибка создания организации:', error);
}
```

## Измененные файлы

- `organizations/serializers.py` - добавлены методы `validate_name()` и `validate_short_name()`

## Чеклист

- [x] Обновлен `organizations/serializers.py`
- [x] Создан тест `test_bug_008_organization_unique_name.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API
- [ ] Уведомлен frontend о новых ошибках валидации

## Альтернативные решения

### Вариант 1: Уникальность на уровне БД
Можно добавить уникальный индекс в модель:
```python
class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True, ...)
```

**Минусы:**
- Не поддерживает регистронезависимую проверку
- Менее информативные сообщения об ошибках
- Требует миграции БД

### Вариант 2: Уникальность в пределах города
Можно разрешить одинаковые названия в разных городах:
```python
queryset = Organization.objects.filter(
    name__iexact=normalized_name,
    city=self.initial_data.get('city')
)
```

## Связанные документы

- `organizations/models.py` - модель Organization
- `organizations/views.py` - OrganizationViewSet
- API_DOCUMENTATION.md - документация API
