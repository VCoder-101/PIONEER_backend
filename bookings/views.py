from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import Booking
from .serializers import BookingSerializer
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
