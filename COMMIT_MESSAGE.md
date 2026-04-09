refactor: убрана роль ORGANIZATION, переход на ownership-подход

- Убраны все проверки role == 'ORGANIZATION' из production-кода
- get_queryset в OrganizationViewSet, ServiceViewSet, ServiceItemViewSet упрощён: ADMIN видит всё, остальные — каталог approved/active
- Для просмотра своих организаций используется /me/
- seed_db: владельцы организаций создаются с role=CLIENT
- Удалены неиспользуемые permissions: IsOwner, IsClient, IsAdminOrOwner, IsAdminOrReadOnly
- В БД обновлены 10 пользователей: ORGANIZATION → CLIENT