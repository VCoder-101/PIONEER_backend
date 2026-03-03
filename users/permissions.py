from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Доступ только для администраторов"""
    message = "Только администраторы имеют доступ к этому ресурсу"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOwner(permissions.BasePermission):
    """Доступ только для владельцев организаций"""
    message = "Только владельцы организаций имеют доступ к этому ресурсу"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ORGANIZATION'


class IsClient(permissions.BasePermission):
    """Доступ только для клиентов"""
    message = "Только клиенты имеют доступ к этому ресурсу"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'CLIENT'


class IsAdminOrOwner(permissions.BasePermission):
    """Доступ для администраторов или владельцев"""
    message = "Только администраторы или владельцы организаций имеют доступ к этому ресурсу"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['ADMIN', 'ORGANIZATION']


class IsAdminOrReadOnly(permissions.BasePermission):
    """Админ может всё, остальные только читать"""
    message = "Только администраторы могут изменять этот ресурс"
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Чтение доступно всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Изменение только для админов
        return request.user.role == 'ADMIN'
