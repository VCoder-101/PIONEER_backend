from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Service, ServiceItem
from .serializers import ServiceSerializer, ServiceItemSerializer
from .permissions import IsServiceOwner


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API для управления услугами.
    - ADMIN: видит все услуги
    - OWNER: видит и управляет услугами своих организаций
    - CLIENT: видит только активные услуги (только чтение)
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated, IsServiceOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['organization', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Service.objects.all()
        elif user.role == 'OWNER':
            return Service.objects.filter(organization__owner=user)
        else:
            # Клиенты видят только активные услуги
            return Service.objects.filter(is_active=True)


class ServiceItemViewSet(viewsets.ModelViewSet):
    """
    API для управления элементами услуг.
    """
    serializer_class = ServiceItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['service', 'is_required', 'is_active']
    ordering_fields = ['order', 'name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ServiceItem.objects.all()
        elif user.role == 'OWNER':
            return ServiceItem.objects.filter(service__organization__owner=user)
        else:
            return ServiceItem.objects.filter(is_active=True, service__is_active=True)
