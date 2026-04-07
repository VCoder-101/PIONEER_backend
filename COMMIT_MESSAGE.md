fix: ограничение доступа к организациям по владельцу + эндпоинт /me/

- Исправлен get_queryset в OrganizationViewSet: ORGANIZATION видит только свои организации
- Добавлен action GET /api/organizations/me/ — возвращает организации текущего пользователя (пагинированный ответ)
- Добавлено создание OrganizationSchedule в seed_db (Пн-Сб рабочие, Вс выходной)