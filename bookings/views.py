from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Booking
from .serializers import BookingSerializer, InvoiceSerializer
from .permissions import IsBookingOwnerOrServiceOwner


class BookingViewSet(viewsets.ModelViewSet):
    """
    API для управления бронированиями.
    - ADMIN: видит все бронирования
    - ORGANIZATION: видит бронирования на услуги своих организаций
    - CLIENT: видит только свои бронирования
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsBookingOwnerOrServiceOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'service']
    search_fields = ['user__email', 'service__title']
    ordering_fields = ['scheduled_at', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Booking.objects.all()
        else:
            # Проверяем, является ли пользователь владельцем организации
            user_organizations = user.organizations.all()
            if user_organizations.exists():
                # Пользователь владеет организациями - показываем брони на его услуги + свои брони
                return Booking.objects.filter(
                    models.Q(service__organization__owner=user) |
                    models.Q(user=user)
                ).distinct()
            else:
                # Обычный клиент - видит только свои бронирования
                return Booking.objects.filter(user=user)

    def perform_create(self, serializer):
        # Автоматически устанавливаем пользователя при создании
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Отменить бронирование.
        Доступно клиенту (своё бронирование), владельцу организации (брони на свои услуги) и администратору.
        """
        booking = self.get_object()
        
        # Проверка прав на отмену
        can_cancel = False
        cancelled_by = None
        
        if request.user.role == 'ADMIN':
            can_cancel = True
            cancelled_by = 'admin'
        elif booking.user == request.user:
            can_cancel = True
            cancelled_by = 'client'
        elif booking.service.organization.owner == request.user:
            can_cancel = True
            cancelled_by = 'organization'
        
        if not can_cancel:
            return Response(
                {'error': 'У вас нет прав на отмену этого бронирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверка статуса - нельзя отменить уже отмененное или завершенное
        if booking.status == 'CANCELLED':
            return Response(
                {'error': 'Бронирование уже отменено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.status == 'DONE':
            return Response(
                {'error': 'Нельзя отменить завершенное бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Отменяем бронирование
        old_status = booking.status
        booking.status = 'CANCELLED'
        booking.save()
        
        serializer = self.get_serializer(booking)
        
        return Response({
            'message': 'Бронирование успешно отменено',
            'cancelled_by': cancelled_by,
            'old_status': old_status,
            'booking': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def calendar(self, request):
        """
        Получить бронирования в календарном формате (invoices).
        Возвращает упрощенный формат для отображения в календаре.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Применяем пагинацию
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = InvoiceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = InvoiceSerializer(queryset, many=True)
        return Response(serializer.data)
