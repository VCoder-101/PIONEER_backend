fix: timezone Europe/Samara, валидация organization_type, seed_db 20 организаций

- TIME_ZONE изменён с UTC на Europe/Samara — слоты и валидация записей теперь по самарскому времени
- availability_views: datetime.now() заменён на timezone.localtime()
- Сериализатор организации: добавлена валидация organization_type, невалидные значения подставляются как wash
- seed_db расширен до 20 организаций: 5 wash, 5 tire, 10 комбинированных
- Исправлено невалидное значение carwash в базе