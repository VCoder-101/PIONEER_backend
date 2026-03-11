from rest_framework import permissions


class IsBookingOwnerOrServiceOwner(permissions.BasePermission):
    """Клиент видит свои брони, владелец - брони на свои услуги"""
    
    def has_permission(self, request, view):
        # Проверяем что пользователь авторизован
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Все авторизованные могут создавать и читать
        return True
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Клиент может управлять своими бронированиями
        if obj.user == request.user:
            return True
        
        # Владелец организации может видеть брони на услуги своей организации
        if obj.service.organization.owner == request.user:
            return True
        
        return False
