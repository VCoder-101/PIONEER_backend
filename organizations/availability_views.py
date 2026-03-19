"""
Views для управления расписанием и доступными слотами
"""
from datetime import datetime, timedelta, time as dt_time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from .availability_models import (
    OrganizationSchedule,
    OrganizationHoliday,
    ServiceAvailability
)
from .availability_serializers import (
    OrganizationScheduleSerializer,
    OrganizationHolidaySerializer,
    ServiceAvailabilitySerializer
)
from bookings.models import Booking


class OrganizationScheduleViewSet(viewsets.ModelViewSet):
    """
    API для управления расписанием организаций
    """
    serializer_class = OrganizationScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return OrganizationSchedule.objects.all()
        else:
            # Владельцы видят расписание своих организаций
            return OrganizationSchedule.objects.filter(organization__owner=user)
    
    def perform_create(self, serializer):
        # Проверяем права на организацию
        organization = serializer.validated_data['organization']
        if self.request.user.role != 'ADMIN' and organization.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Вы можете создавать расписание только для своих организаций")
        serializer.save()


class OrganizationHolidayViewSet(viewsets.ModelViewSet):
    """
    API для управления выходными днями организаций
    """
    serializer_class = OrganizationHolidaySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return OrganizationHoliday.objects.all()
        else:
            return OrganizationHoliday.objects.filter(organization__owner=user)
    
    def perform_create(self, serializer):
        organization = serializer.validated_data['organization']
        if self.request.user.role != 'ADMIN' and organization.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Вы можете создавать выходные только для своих организаций")
        serializer.save()


class ServiceAvailabilityViewSet(viewsets.ModelViewSet):
    """
    API для управления доступностью услуг
    """
    serializer_class = ServiceAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ServiceAvailability.objects.all()
        else:
            return ServiceAvailability.objects.filter(service__organization__owner=user)
    
    def perform_create(self, serializer):
        service = serializer.validated_data['service']
        if self.request.user.role != 'ADMIN' and service.organization.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Вы можете создавать правила только для услуг своих организаций")
        serializer.save()


class AvailableSlotsViewSet(viewsets.ViewSet):
    """
    API для получения доступных слотов для записи
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def for_service(self, request):
        """
        Получить доступные слоты для услуги на указанную дату
        
        Query params:
        - service_id: ID услуги (обязательно)
        - date: дата в формате YYYY-MM-DD (обязательно)
        """
        from services.models import Service
        
        service_id = request.query_params.get('service_id')
        date_str = request.query_params.get('date')
        
        if not service_id or not date_str:
            return Response(
                {'error': 'Требуются параметры service_id и date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response(
                {'error': 'Услуга не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты. Используйте YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, не прошедшая ли дата
        if target_date < datetime.now().date():
            return Response(
                {'error': 'Нельзя записаться на прошедшую дату'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Генерируем слоты
        slots = self._generate_slots(service, target_date)
        
        return Response({
            'service_id': service.id,
            'service_title': service.title,
            'organization': service.organization.name,
            'date': date_str,
            'duration': service.duration,
            'slots': slots
        })
    
    def _generate_slots(self, service, target_date):
        """
        Генерирует список доступных слотов для услуги на указанную дату
        """
        from django.utils import timezone
        
        organization = service.organization
        weekday = target_date.weekday()
        
        # Проверяем выходной день
        if OrganizationHoliday.objects.filter(
            organization=organization,
            date=target_date,
            is_active=True
        ).exists():
            return []
        
        # Получаем расписание организации
        try:
            schedule = OrganizationSchedule.objects.get(
                organization=organization,
                weekday=weekday,
                is_active=True
            )
        except OrganizationSchedule.DoesNotExist:
            # Нет расписания для этого дня
            return []
        
        if not schedule.is_working_day:
            return []
        
        # Проверяем специфичное расписание услуги
        service_availability = ServiceAvailability.objects.filter(
            service=service,
            weekday=weekday,
            is_active=True
        ).first()
        
        if service_availability:
            start_time = service_availability.available_from
            end_time = service_availability.available_to
            max_bookings = service_availability.max_bookings_per_slot
        else:
            start_time = schedule.open_time
            end_time = schedule.close_time
            max_bookings = 1
        
        # Генерируем слоты
        slots = []
        slot_duration = timedelta(minutes=schedule.slot_duration)
        service_duration = timedelta(minutes=service.duration)
        
        # Используем timezone-aware datetime
        current_time = timezone.make_aware(datetime.combine(target_date, start_time))
        end_datetime = timezone.make_aware(datetime.combine(target_date, end_time))
        
        # Если это сегодня, начинаем с текущего времени + 1 час
        now = timezone.now()
        if target_date == now.date():
            min_time = now + timedelta(hours=1)
            if current_time < min_time:
                current_time = min_time
                # Округляем до ближайшего слота
                minutes = (current_time.minute // schedule.slot_duration + 1) * schedule.slot_duration
                current_time = current_time.replace(minute=0, second=0, microsecond=0)
                current_time += timedelta(minutes=minutes)
        
        while current_time + service_duration <= end_datetime:
            slot_time = current_time.time()
            
            # Проверяем перерыв
            if schedule.break_start and schedule.break_end:
                if schedule.break_start <= slot_time < schedule.break_end:
                    current_time += slot_duration
                    continue
            
            # Проверяем занятость слота
            existing_bookings = Booking.objects.filter(
                service=service,
                scheduled_at=current_time,
                status__in=['NEW', 'CONFIRMED']
            ).count()
            
            is_available = existing_bookings < max_bookings
            
            slots.append({
                'time': slot_time.strftime('%H:%M'),
                'datetime': current_time.isoformat(),
                'available': is_available,
                'booked': existing_bookings,
                'capacity': max_bookings
            })
            
            current_time += slot_duration
        
        return slots
