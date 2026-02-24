from rest_framework import permissions


class IsOrganizationOwner(permissions.BasePermission):
    """Владелец может управлять только своей организацией"""
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец может управлять только своей организацией
        if request.user.role == 'ORGANIZATION':
            return obj.owner == request.user
        
        # Чтение доступно всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
