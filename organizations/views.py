from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
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
    - ORGANIZATION: видит только свои организации
    - CLIENT: видит все организации (только чтение)
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'is_active', 'organization_status', 'organization_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Organization.objects.all()
        else:
            # Владельцы организаций видят свои организации
            user_organizations = user.organizations.all()
            if user_organizations.exists():
                return user_organizations
            else:
                # Обычные клиенты видят только активные одобренные организации
                return Organization.objects.filter(is_active=True, organization_status='approved')
    
    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца при создании
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Одобрить заявку организации (только для администраторов)"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Только администраторы могут одобрять заявки'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization = self.get_object()
        organization.organization_status = 'approved'
        organization.organization_date_approved = timezone.now()
        organization.save()
        
        serializer = self.get_serializer(organization)
        return Response({
            'message': 'Заявка одобрена',
            'organization': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Отклонить заявку организации (только для администраторов)"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Только администраторы могут отклонять заявки'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        organization = self.get_object()
        organization.organization_status = 'rejected'
        organization.organization_date_approved = None
        organization.save()
        
        serializer = self.get_serializer(organization)
        return Response({
            'message': 'Заявка отклонена',
            'organization': serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Отменить заявку на регистрацию организации (только для владельца).
        Доступно только для заявок со статусом 'pending'.
        """
        organization = self.get_object()
        
        # Проверка прав: только владелец или админ
        if organization.owner != request.user and request.user.role != 'ADMIN':
            return Response(
                {'error': 'У вас нет прав на отмену этой заявки'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверка статуса: можно отменить только заявки на рассмотрении
        if organization.organization_status != 'pending':
            return Response(
                {
                    'error': f'Нельзя отменить заявку со статусом "{organization.get_organization_status_display()}". '
                            'Отменить можно только заявки на рассмотрении.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Отменяем заявку (меняем статус на rejected)
        old_status = organization.organization_status
        organization.organization_status = 'rejected'
        organization.organization_date_approved = None
        organization.save()
        
        serializer = self.get_serializer(organization)
        
        return Response({
            'message': 'Заявка на регистрацию организации успешно отменена',
            'old_status': old_status,
            'organization': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Получить все заявки на рассмотрении (только для администраторов)"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Только администраторы могут просматривать заявки'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_organizations = Organization.objects.filter(organization_status='pending')
        serializer = self.get_serializer(pending_organizations, many=True)
        return Response({
            'count': pending_organizations.count(),
            'results': serializer.data
        })