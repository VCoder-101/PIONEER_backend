from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Доступ только для администраторов"""
    message = "Только администраторы имеют доступ к этому ресурсу"

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'
