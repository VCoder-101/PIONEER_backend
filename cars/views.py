from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError, PermissionDenied

from .models import Car
from .serializers import CarReadSerializer, CarWriteSerializer
from .permissions import IsCarOwnerOrAdmin
from . import services


class CarViewSet(viewsets.ModelViewSet):
    """
    API для управления автомобилями пользователя.
    - ADMIN: видит все автомобили в системе
    - CLIENT: видит и управляет только своими
    """
    permission_classes = [IsCarOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return CarReadSerializer
        return CarWriteSerializer

    def get_queryset(self):
        return services.get_user_cars(self.request.user)

    def get_object(self):
        car = services.get_car_for_user(self.kwargs['pk'], self.request.user)
        if car is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Автомобиль не найден.')
        self.check_object_permissions(self.request, car)
        return car

    def create(self, request, *args, **kwargs):
        serializer = CarWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            car = services.create_car(
                user=request.user,
                **serializer.validated_data
            )
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(CarReadSerializer(car).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        car = self.get_object()
        serializer = CarWriteSerializer(car, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            updated_car = services.update_car(car, request.user, serializer.validated_data)
        except (ValidationError, PermissionDenied) as e:
            error = e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        return Response(CarReadSerializer(updated_car).data)

    def destroy(self, request, *args, **kwargs):
        car = self.get_object()
        try:
            services.delete_car(car, request.user)
        except PermissionDenied as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_204_NO_CONTENT)
