from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Доступ только для администраторов"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOwner(permissions.BasePermission):
    """Доступ только для владельцев организаций"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'OWNER'


class IsClient(permissions.BasePermission):
    """Доступ только для клиентов"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CLIENT'


class IsAdminOrOwner(permissions.BasePermission):
    """Доступ для администраторов или владельцев"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'OWNER']
