from rest_framework import permissions


class IsServiceOwner(permissions.BasePermission):
    """Владелец организации может управлять услугами своей организации"""
    
    def has_permission(self, request, view):
        # Проверяем что пользователь авторизован
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец организации (CLIENT с одобренной организацией) может создавать и управлять
        if hasattr(request.user, 'organizations'):
            # Проверяем наличие хотя бы одной одобренной организации
            approved_orgs = request.user.organizations.filter(organization_status='approved')
            if approved_orgs.exists():
                return True
        
        # Обычные клиенты могут только читать
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Админ может всё
        if request.user.role == 'ADMIN':
            return True
        
        # Владелец организации может управлять услугами своей организации
        if obj.organization.owner == request.user:
            return True
        
        # Чтение доступно всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
