from rest_framework import permissions


class IsServiceOwner(permissions.BasePermission):
    """Владелец организации может управлять услугами своей организации"""
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец может управлять услугами своей организации
        if request.user.role == 'OWNER':
            return obj.organization.owner == request.user
        
        # Чтение доступно всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
