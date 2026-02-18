from rest_framework import permissions


class IsBookingOwnerOrServiceOwner(permissions.BasePermission):
    """Клиент видит свои брони, владелец - брони на свои услуги"""
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Клиент может управлять своими бронированиями
        if request.user.role == 'CLIENT':
            return obj.user == request.user
        
        # Владелец может видеть брони на услуги своей организации
        if request.user.role == 'OWNER':
            return obj.service.organization.owner == request.user
        
        return False
