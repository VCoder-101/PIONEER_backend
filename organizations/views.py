from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Organization, City
from .serializers import OrganizationSerializer, CitySerializer
from .permissions import IsOrganizationOwner


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для просмотра городов.
    Только чтение для всех авторизованных пользователей.
    """
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'region']
    ordering_fields = ['name']


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API для управления организациями.
    - ADMIN: видит все организации
    - OWNER: видит только свои организации
    - CLIENT: видит все организации (только чтение)
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Organization.objects.all()
        elif user.role == 'OWNER':
            return Organization.objects.filter(owner=user)
        else:
            return Organization.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца при создании
        serializer.save(owner=self.request.user)
