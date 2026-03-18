# БАГ-006: Исправление подсчета количества и суммы услуг организации

**ID:** BUG-006  
**Приоритет:** P1 (Высокий)  
**Статус:** ✅ Исправлено и протестировано

## Проблема

При запросе `/api/organizations/{id}/` поля `countServices` и `summaryPrice` не приходили в ответе или возвращали неактуальные значения (всегда 0).

### Причина
Поля `count_services` и `summary_price` в модели `Organization` - это статические поля в БД, которые не обновлялись автоматически при создании/изменении услуг.

```python
# Статические поля в БД (не обновляются автоматически)
count_services = models.IntegerField(default=0, verbose_name='Количество услуг')
summary_price = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    default=0, 
    verbose_name='Итоговая стоимость'
)
```

## Решение

Изменены поля `countServices` и `summaryPrice` в `OrganizationSerializer` на `SerializerMethodField` для динамического вычисления значений из связанных услуг.

### Было
```python
countServices = serializers.IntegerField(source='count_services', read_only=True)
summaryPrice = serializers.DecimalField(
    source='summary_price', 
    max_digits=10, 
    decimal_places=2, 
    read_only=True
)
```

### Стало
```python
countServices = serializers.SerializerMethodField()
summaryPrice = serializers.SerializerMethodField()

def get_countServices(self, obj):
    """Вычисляет количество активных услуг организации"""
    return obj.services.filter(is_active=True).count()

def get_summaryPrice(self, obj):
    """Вычисляет суммарную стоимость всех активных услуг организации"""
    from django.db.models import Sum
    total = obj.services.filter(is_active=True).aggregate(total=Sum('price'))['total']
    return str(total) if total else "0.00"
```

## Как работает

### Динамическое вычисление
- `countServices` - подсчитывает количество активных услуг (`is_active=True`)
- `summaryPrice` - суммирует цены всех активных услуг

### Преимущества
- ✅ Всегда актуальные данные
- ✅ Автоматически обновляется при изменении услуг
- ✅ Учитывает только активные услуги
- ✅ Не требует ручного обновления полей в БД

### Недостатки
- ⚠️ Дополнительный запрос к БД при каждом запросе организации
- ⚠️ Для оптимизации можно использовать `select_related()` или кэширование

## Тестирование

### Автоматический тест
```bash
python test_bug_006_organization_stats.py
```

### Результат
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БАГ-006 ИСПРАВЛЕН!
```

### Что проверяет тест
1. ✅ Начальные значения (без услуг): countServices=0, summaryPrice=0.00
2. ✅ После создания 3 услуг: countServices=3, summaryPrice=4500.00
3. ✅ После деактивации 1 услуги: countServices=2, summaryPrice=3500.00

## Пример ответа API

### GET /api/organizations/1/

**До исправления:**
```json
{
  "id": 1,
  "name": "My Organization",
  "countServices": 0,
  "summaryPrice": "0.00",
  ...
}
```
(Всегда 0, даже если есть услуги)

**После исправления:**
```json
{
  "id": 1,
  "name": "My Organization",
  "countServices": 3,
  "summaryPrice": "4500.00",
  ...
}
```
(Актуальные значения из БД)

## Измененные файлы

- `organizations/serializers.py` - обновлен `OrganizationSerializer`

## Чеклист

- [x] Обновлен `organizations/serializers.py`
- [x] Создан тест `test_bug_006_organization_stats.py`
- [x] Проверен код на ошибки (getDiagnostics)
- [x] Запущен тест - ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ
- [ ] Обновлена документация API

## Оптимизация (опционально)

Для улучшения производительности можно добавить prefetch в ViewSet:

```python
class OrganizationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        # Предзагрузка услуг для оптимизации
        return queryset.prefetch_related('services')
```

Или использовать аннотации:

```python
from django.db.models import Count, Sum

def get_queryset(self):
    return Organization.objects.annotate(
        services_count=Count('services', filter=Q(services__is_active=True)),
        services_sum=Sum('services__price', filter=Q(services__is_active=True))
    )
```

## Связанные документы

- `organizations/models.py` - модель Organization
- `services/models.py` - модель Service
- API_DOCUMENTATION.md - документация API
