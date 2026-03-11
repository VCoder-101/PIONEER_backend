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
        
        # Владельцы организаций могут создавать и читать
        if hasattr(request.user, 'organizations') and request.user.organizations.exists():
            return True
        
        # Клиенты могут только читать
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец может управлять только своей организацией
        if obj.owner == request.user:
            return True
        
        # Чтение доступно всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
