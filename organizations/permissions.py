from rest_framework import permissions


class IsOrganizationOwner(permissions.BasePermission):
    """Владелец может управлять только своей организацией"""
    
    def has_permission(self, request, view):
        # Проверяем что пользователь авторизован
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец может создавать и читать
        if request.user.role == 'ORGANIZATION':
            return True
        
        # Клиенты могут только читать
        if request.user.role == 'CLIENT' and request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
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
