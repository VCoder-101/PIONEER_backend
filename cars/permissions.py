from rest_framework.permissions import BasePermission


class IsCarOwnerOrAdmin(BasePermission):
    """
    Разрешение: ADMIN видит и управляет всем,
    остальные — только своими автомобилями.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'ADMIN':
            return True
        return obj.user == request.user
