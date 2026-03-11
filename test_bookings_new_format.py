#!/usr/bin/env python
"""
Тест нового формата API бронирований
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from organizations.models import Organization
from services.models import Service
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from django.utils import timezone
from datetime import timedelta

def test_new_booking_format():
    print("=== Тест нового формата API бронирований ===")
    
    # Найдем или создадим пользователя с именем
    user, created = User.objects.get_or_create(
        email='client_with_name@test.com',
        defaults={
            'role': 'CLIENT',
            'name': 'Иван Петров'
        }
    )
    if not user.name:
        user.name = 'Иван Петров'
        user.save()
    
    print(f"Клиент: {user.name} ({user.email})")
    
    # Найдем услугу
    service = Service.objects.first()
    if not service:
        print("Нет услуг для создания бронирования")
        return
    
    # Создадим тестовые бронирования с новыми полями
    bookings_data = [
        {
            'user': user,
            'service': service,
            'status': 'CONFIRMED',
            'scheduled_at': timezone.now() + timedelta(days=1, hours=10, minutes=30),
            'car_model': 'Lada Vesta',
            'wheel_diameter': 16
        },
        {
            'user': user,
            'service': service,
            'status': 'NEW',
            'scheduled_at': timezone.now() + timedelta(days=2, hours=14, minutes=0),
            'car_model': 'Lada Granta',
            'wheel_diameter': 15
        }
    ]
    
    created_bookings = []
    for data in bookings_data:
        booking, created = Booking.objects.get_or_create(
            user=data['user'],
            service=data['service'],
            scheduled_at=data['scheduled_at'],
            defaults=data
        )
        created_bookings.append(booking)
        print(f"Бронирование: {booking.car_model} - {'создано' if created else 'найдено'}")
    
    # Тестируем сериализацию в новом формате
    print("\n=== Новый формат API ===")
    serializer = BookingSerializer(created_bookings, many=True)
    
    import json
    
    # Создаем ответ в требуемом формате
    invoices = []
    for booking_data in serializer.data:
        invoice = {
            'id': booking_data['id'],
            'customerName': booking_data['customerName'],
            'dateTime': booking_data['dateTime'],
            'carModel': booking_data['carModel'],
            'serviceMethod': booking_data['serviceMethod'],
            'duration': str(booking_data['duration']),
            'price': float(booking_data['price']) if booking_data['price'] else 0
        }
        invoices.append(invoice)
    
    print("Формат invoices:")
    print(json.dumps(invoices, indent=2, ensure_ascii=False))
    
    # Полный API ответ
    print(f"\n=== Полный API ответ ===")
    api_response = {
        "count": len(serializer.data),
        "next": None,
        "previous": None,
        "results": serializer.data
    }
    print(json.dumps(api_response, indent=2, ensure_ascii=False, default=str))

if __name__ == '__main__':
    test_new_booking_format()