from django.core.exceptions import ValidationError, PermissionDenied
from .models import Car


def get_user_cars(user):
    """
    Возвращает автомобили пользователя.
    ADMIN видит все, CLIENT — только свои.
    """
    if user.role == 'ADMIN':
        return Car.objects.select_related('user').all()
    return Car.objects.filter(user=user)


def get_car_for_user(car_id, user):
    """
    Получить конкретный автомобиль.
    Пользователь может видеть только свои, ADMIN — любой.
    """
    try:
        car = Car.objects.select_related('user').get(pk=car_id)
    except Car.DoesNotExist:
        return None

    if user.role == 'ADMIN' or car.user == user:
        return car
    return None


def create_car(user, brand, license_plate, wheel_diameter):
    """
    Создать автомобиль для пользователя.
    """
    if Car.objects.filter(license_plate=license_plate).exists():
        raise ValidationError({'license_plate': 'Автомобиль с таким госномером уже зарегистрирован в системе.'})

    return Car.objects.create(
        user=user,
        brand=brand,
        license_plate=license_plate,
        wheel_diameter=wheel_diameter,
    )


def update_car(car, user, data):
    """
    Обновить автомобиль. Только владелец или ADMIN.
    """
    if user.role != 'ADMIN' and car.user != user:
        raise PermissionDenied('Вы можете редактировать только свои автомобили.')

    # Проверяем уникальность госномера, если он меняется
    new_plate = data.get('license_plate')
    if new_plate and new_plate != car.license_plate:
        if Car.objects.filter(license_plate=new_plate).exists():
            raise ValidationError({'license_plate': 'Автомобиль с таким госномером уже зарегистрирован в системе.'})

    for field, value in data.items():
        setattr(car, field, value)
    car.save()
    return car


def delete_car(car, user):
    """
    Удалить автомобиль. Только владелец или ADMIN.
    """
    if user.role != 'ADMIN' and car.user != user:
        raise PermissionDenied('Вы можете удалять только свои автомобили.')
    car.delete()
