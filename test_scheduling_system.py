"""
Тестовый скрипт для проверки системы управления расписанием и слотами
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from datetime import datetime, timedelta
from organizations.models import Organization, OrganizationSchedule, OrganizationHoliday
from services.models import Service
from organizations.availability_models import ServiceAvailability
from users.models import User


def test_scheduling_system():
    print("=" * 80)
    print("ТЕСТ СИСТЕМЫ УПРАВЛЕНИЯ РАСПИСАНИЕМ И СЛОТАМИ")
    print("=" * 80)
    
    # 1. Находим тестовую организацию
    print("\n1. Поиск тестовой организации...")
    org = Organization.objects.filter(is_active=True).first()
    if not org:
        print("❌ Нет активных организаций")
        return
    print(f"✅ Найдена организация: {org.name} (ID: {org.id})")
    
    # 2. Создаем расписание для организации
    print("\n2. Создание расписания...")
    
    # Удаляем старое расписание если есть
    OrganizationSchedule.objects.filter(organization=org).delete()
    
    # Понедельник-пятница: 9:00-18:00 с перерывом
    for weekday in range(5):
        schedule = OrganizationSchedule.objects.create(
            organization=org,
            weekday=weekday,
            is_working_day=True,
            open_time='09:00',
            close_time='18:00',
            break_start='13:00',
            break_end='14:00',
            slot_duration=30
        )
        print(f"✅ Создано расписание для {schedule.get_weekday_display()}")
    
    # Суббота: 10:00-16:00 без перерыва
    schedule = OrganizationSchedule.objects.create(
        organization=org,
        weekday=5,
        is_working_day=True,
        open_time='10:00',
        close_time='16:00',
        slot_duration=30
    )
    print(f"✅ Создано расписание для {schedule.get_weekday_display()}")
    
    # Воскресенье: выходной
    schedule = OrganizationSchedule.objects.create(
        organization=org,
        weekday=6,
        is_working_day=False,
        open_time='00:00',
        close_time='00:00',
        slot_duration=30
    )
    print(f"✅ Создано расписание для {schedule.get_weekday_display()} (выходной)")
    
    # 3. Добавляем праздничный день
    print("\n3. Добавление праздничного дня...")
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    # Удаляем старые выходные если есть
    OrganizationHoliday.objects.filter(organization=org).delete()
    
    holiday = OrganizationHoliday.objects.create(
        organization=org,
        date=tomorrow,
        reason='Тестовый выходной'
    )
    print(f"✅ Добавлен выходной: {holiday.date} - {holiday.reason}")
    
    # 4. Находим услугу
    print("\n4. Поиск услуги организации...")
    service = Service.objects.filter(organization=org, is_active=True).first()
    if not service:
        print("❌ Нет активных услуг для этой организации")
        return
    print(f"✅ Найдена услуга: {service.title} (ID: {service.id})")
    print(f"   Длительность: {service.duration} мин, Цена: {service.price} руб")
    
    # 5. Создаем специальное расписание для услуги
    print("\n5. Создание специального расписания для услуги...")
    
    # Удаляем старые правила если есть
    ServiceAvailability.objects.filter(service=service).delete()
    
    # Понедельник: услуга доступна 10:00-17:00, можно 2 записи одновременно
    availability = ServiceAvailability.objects.create(
        service=service,
        weekday=0,
        available_from='10:00',
        available_to='17:00',
        max_bookings_per_slot=2
    )
    print(f"✅ Создано правило для {availability.get_weekday_display()}")
    print(f"   Доступна: {availability.available_from} - {availability.available_to}")
    print(f"   Макс. записей на слот: {availability.max_bookings_per_slot}")
    
    # 6. Проверяем статистику
    print("\n6. Статистика:")
    print(f"   Расписаний: {OrganizationSchedule.objects.filter(organization=org).count()}")
    print(f"   Выходных дней: {OrganizationHoliday.objects.filter(organization=org).count()}")
    print(f"   Правил доступности: {ServiceAvailability.objects.filter(service=service).count()}")
    
    # 7. Тестируем генерацию слотов
    print("\n7. Тестирование генерации слотов...")
    from organizations.availability_views import AvailableSlotsViewSet
    
    viewset = AvailableSlotsViewSet()
    
    # Тест на завтра (выходной)
    print(f"\n   Тест 1: Завтра ({tomorrow}) - должно быть 0 слотов (выходной)")
    slots = viewset._generate_slots(service, tomorrow)
    print(f"   Результат: {len(slots)} слотов")
    if len(slots) == 0:
        print("   ✅ Корректно - выходной день")
    else:
        print("   ❌ Ошибка - должно быть 0 слотов")
    
    # Тест на послезавтра
    day_after_tomorrow = tomorrow + timedelta(days=1)
    weekday = day_after_tomorrow.weekday()
    weekday_name = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'][weekday]
    
    print(f"\n   Тест 2: Послезавтра ({day_after_tomorrow}, {weekday_name})")
    slots = viewset._generate_slots(service, day_after_tomorrow)
    print(f"   Результат: {len(slots)} слотов")
    
    if len(slots) > 0:
        print("   ✅ Слоты сгенерированы")
        print(f"\n   Первые 5 слотов:")
        for slot in slots[:5]:
            status = "🟢 Доступен" if slot['available'] else "🔴 Занят"
            print(f"      {slot['time']} - {status} ({slot['booked']}/{slot['capacity']})")
        
        if len(slots) > 5:
            print(f"   ... и еще {len(slots) - 5} слотов")
    else:
        if weekday == 6:
            print("   ✅ Корректно - воскресенье (выходной)")
        else:
            print("   ⚠️  Нет слотов (возможно, день уже прошел или нет расписания)")
    
    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)
    print("\nДля проверки через API используйте:")
    print(f"GET /api/organizations/available-slots/for_service/?service_id={service.id}&date={day_after_tomorrow}")
    print("\nДля просмотра в админке:")
    print("- Расписания: /admin/organizations/organizationschedule/")
    print("- Выходные: /admin/organizations/organizationholiday/")
    print("- Доступность услуг: /admin/organizations/serviceavailability/")


if __name__ == '__main__':
    test_scheduling_system()
