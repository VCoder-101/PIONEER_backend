"""
Команда заполнения базы тестовыми данными.
Идемпотентна — повторный запуск не дублирует записи.

Создаёт:
  - 1 город (Самара)
  - 10 организаций с владельцами (роль ORGANIZATION)
  - 2 услуги на организацию (Мойка, Шиномонтаж) с позициями ServiceItem
  - 20 клиентов (роль CLIENT)
  - 15 бронирований в разных статусах и датах
"""

import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, BookingItem
from organizations.models import City, Organization
from services.models import Service, ServiceItem

User = get_user_model()

# ---------------------------------------------------------------------------
# Справочные данные
# ---------------------------------------------------------------------------

ORGANIZATIONS = [
    {
        "name": "Чистый Кузов",
        "address": "ул. Московское шоссе, 100",
        "phone": "+7 846 200-10-01",
        "email": "chistiy-kuzov@samara.local",
        "description": "Профессиональная мойка и полировка кузова любой сложности.",
    },
    {
        "name": "АвтоБлеск",
        "address": "ул. Ново-Садовая, 265",
        "phone": "+7 846 200-10-02",
        "email": "avtoblsk@samara.local",
        "description": "Ручная и автоматическая мойка, химчистка салона.",
    },
    {
        "name": "Шин-Сервис Плюс",
        "address": "пр. Кирова, 45",
        "phone": "+7 846 200-10-03",
        "email": "shin-service@samara.local",
        "description": "Шиномонтаж, балансировка, сезонное хранение шин.",
    },
    {
        "name": "Мойка на Московском",
        "address": "Московское шоссе, 332",
        "phone": "+7 846 200-10-04",
        "email": "moyka-msk@samara.local",
        "description": "Быстрая мойка рядом с выездом на трассу М5.",
    },
    {
        "name": "АвтоМойка Престиж",
        "address": "ул. Победы, 78",
        "phone": "+7 846 200-10-05",
        "email": "prestige-auto@samara.local",
        "description": "Премиальный сервис: детейлинг, защитные покрытия.",
    },
    {
        "name": "Колесо",
        "address": "ул. Авроры, 110",
        "phone": "+7 846 200-10-06",
        "email": "koleso-samara@samara.local",
        "description": "Полный спектр шиномонтажных работ, правка дисков.",
    },
    {
        "name": "Экспресс Мойка",
        "address": "ул. Советской Армии, 185",
        "phone": "+7 846 200-10-07",
        "email": "express-moyka@samara.local",
        "description": "Мойка за 20 минут — без записи, всегда свободно.",
    },
    {
        "name": "АвтоСервис Маяк",
        "address": "ул. Стара-Загора, 52",
        "phone": "+7 846 200-10-08",
        "email": "mayak-auto@samara.local",
        "description": "Мойка, шиномонтаж и мелкий ремонт в одном месте.",
    },
    {
        "name": "Шинный Мастер",
        "address": "пр. Металлургов, 68",
        "phone": "+7 846 200-10-09",
        "email": "shin-master@samara.local",
        "description": "Специализируемся на грузовых и легковых шинах.",
    },
    {
        "name": "Кристалл Авто",
        "address": "ул. Промышленности, 302",
        "phone": "+7 846 200-10-10",
        "email": "kristall-avto@samara.local",
        "description": "Мойка, полировка, нанесение керамики.",
    },
]

# Базовые позиции услуги "Мойка" (название, базовая цена, мин)
WASH_ITEMS = [
    ("Мойка кузова", Decimal("350"), 30),
    ("Пылесос салона", Decimal("250"), 20),
    ("Полная мойка (кузов + салон)", Decimal("700"), 50),
    ("Мойка днища", Decimal("300"), 25),
    ("Мойка двигателя", Decimal("600"), 40),
    ("Химчистка салона", Decimal("3000"), 180),
    ("Полировка кузова", Decimal("4500"), 240),
]

# Базовые позиции услуги "Шиномонтаж" (название, базовая цена, мин)
TIRE_ITEMS = [
    ("Замена 4 колёс", Decimal("1000"), 60),
    ("Балансировка (4 колеса)", Decimal("500"), 30),
    ("Ремонт прокола", Decimal("300"), 20),
    ("Замена вентилей (4 шт.)", Decimal("160"), 15),
    ("Сезонное хранение шин", Decimal("2000"), 10),
    ("Правка диска", Decimal("700"), 45),
]

# 20 клиентов — имена и фамилии
CLIENTS = [
    ("Александр Иванов",    "client01@pioneer.local"),
    ("Дмитрий Петров",      "client02@pioneer.local"),
    ("Иван Сидоров",        "client03@pioneer.local"),
    ("Сергей Козлов",       "client04@pioneer.local"),
    ("Михаил Новиков",      "client05@pioneer.local"),
    ("Андрей Морозов",      "client06@pioneer.local"),
    ("Алексей Попов",       "client07@pioneer.local"),
    ("Николай Лебедев",     "client08@pioneer.local"),
    ("Евгений Ковалёв",     "client09@pioneer.local"),
    ("Владимир Зайцев",     "client10@pioneer.local"),
    ("Анастасия Соколова",  "client11@pioneer.local"),
    ("Екатерина Кузнецова", "client12@pioneer.local"),
    ("Мария Волкова",       "client13@pioneer.local"),
    ("Ольга Смирнова",      "client14@pioneer.local"),
    ("Татьяна Богданова",   "client15@pioneer.local"),
    ("Наталья Васильева",   "client16@pioneer.local"),
    ("Елена Фёдорова",      "client17@pioneer.local"),
    ("Юлия Орлова",         "client18@pioneer.local"),
    ("Светлана Чернова",    "client19@pioneer.local"),
    ("Ирина Захарова",      "client20@pioneer.local"),
]

BOOKING_STATUSES = ["NEW", "CONFIRMED", "CANCELLED", "DONE"]


def _vary(base_price: Decimal, factor: float) -> Decimal:
    """Применяет коэффициент к цене и округляет до рублей."""
    result = base_price * Decimal(str(round(factor, 3)))
    return result.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Заполнить базу тестовыми данными (идемпотентно)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("=== seed_db: начало ===")

        # 1. Город
        city = self._seed_city()

        # 2. Организации + владельцы
        orgs = self._seed_organizations(city)

        # 3. Услуги и позиции
        all_services = self._seed_services(orgs)

        # 4. Клиенты
        clients = self._seed_clients()

        # 5. Бронирования
        self._seed_bookings(clients, all_services)

        self.stdout.write(self.style.SUCCESS("=== seed_db: готово ==="))

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _seed_city(self) -> City:
        city, created = City.objects.get_or_create(
            name="Самара",
            defaults={
                "region": "Самарская область",
                "country": "Россия",
                "is_active": True,
            },
        )
        status = "создан" if created else "уже существует"
        self.stdout.write(f"  Город «Самара» — {status}")
        return city

    def _seed_organizations(self, city: City) -> list[Organization]:
        orgs = []
        for idx, data in enumerate(ORGANIZATIONS, start=1):
            # Владелец организации
            owner_email = f"org{idx:02d}@pioneer.local"
            owner, owner_created = User.objects.get_or_create(
                email=owner_email,
                defaults={
                    "name": f"Владелец {data['name']}",
                    "role": "ORGANIZATION",
                    "is_active": True,
                },
            )

            # Организация — ключ: name
            org, org_created = Organization.objects.get_or_create(
                name=data["name"],
                defaults={
                    "owner": owner,
                    "city": city,
                    "address": data["address"],
                    "phone": data["phone"],
                    "email": data["email"],
                    "description": data["description"],
                    "is_active": True,
                    "organization_status": "approved",
                },
            )
            # Одобряем уже существующие организации (get_or_create не обновляет defaults)
            if org.organization_status != "approved":
                org.organization_status = "approved"
                org.save(update_fields=["organization_status", "organization_date_approved"])
            status = "создана" if org_created else "уже существует"
            self.stdout.write(f"  Организация «{org.name}» — {status}")
            orgs.append(org)

        return orgs

    def _seed_services(self, orgs: list[Organization]) -> list[Service]:
        """
        Создаёт 2 услуги на каждую организацию и позиции с немного
        отличающимися ценами (±10-20% через детерминированный коэффициент).
        """
        # Коэффициенты — уникальные для каждой организации, но стабильные
        # между запусками (индекс в списке, не random)
        factors = [0.85, 0.90, 0.95, 1.00, 1.05, 1.08, 1.10, 1.13, 1.16, 1.20]

        all_services: list[Service] = []

        for idx, org in enumerate(orgs):
            factor = factors[idx % len(factors)]

            # Услуга «Мойка»
            wash_service = self._get_or_create_service(
                org=org,
                title="Мойка",
                description="Ручная и автоматическая мойка автомобиля.",
                base_price=Decimal("500"),
                duration=60,
                factor=factor,
            )
            self._seed_service_items(wash_service, WASH_ITEMS, factor)
            all_services.append(wash_service)

            # Услуга «Шиномонтаж»
            tire_service = self._get_or_create_service(
                org=org,
                title="Шиномонтаж",
                description="Полный спектр шиномонтажных работ.",
                base_price=Decimal("1000"),
                duration=90,
                factor=factor,
            )
            self._seed_service_items(tire_service, TIRE_ITEMS, factor)
            all_services.append(tire_service)

        return all_services

    def _get_or_create_service(
        self,
        org: Organization,
        title: str,
        description: str,
        base_price: Decimal,
        duration: int,
        factor: float,
    ) -> Service:
        service, created = Service.objects.get_or_create(
            organization=org,
            title=title,
            defaults={
                "description": description,
                "price": _vary(base_price, factor),
                "duration": duration,
                "is_active": True,
            },
        )
        status = "создана" if created else "уже существует"
        self.stdout.write(f"    Услуга «{title}» ({org.name}) — {status}")
        return service

    def _seed_service_items(
        self,
        service: Service,
        items_data: list[tuple],
        factor: float,
    ) -> None:
        for order, (name, base_price, _duration) in enumerate(items_data):
            ServiceItem.objects.get_or_create(
                service=service,
                name=name,
                defaults={
                    "price": _vary(base_price, factor),
                    "is_required": False,
                    "is_active": True,
                    "order": order,
                },
            )

    def _seed_clients(self) -> list[User]:
        clients = []
        for name, email in CLIENTS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": name,
                    "role": "CLIENT",
                    "is_active": True,
                },
            )
            status = "создан" if created else "уже существует"
            self.stdout.write(f"  Клиент {name} ({email}) — {status}")
            clients.append(user)
        return clients

    def _seed_bookings(
        self,
        clients: list[User],
        services: list[Service],
    ) -> None:
        """
        Создаёт 15 бронирований с разными статусами и датами.
        Идемпотентность: пропускаем, если бронирование
        (user, service, scheduled_at) уже существует.
        """
        now = timezone.now()

        # Заранее определённые смещения в днях (отрицательные — прошлое)
        schedule_offsets = [
            -30, -21, -14, -10, -7, -5, -3, -2, -1,
            0, 1, 2, 5, 10, 20,
        ]
        statuses = [
            "DONE", "DONE", "DONE", "DONE", "DONE",
            "CANCELLED", "CANCELLED",
            "CONFIRMED", "CONFIRMED",
            "NEW",
            "CONFIRMED", "NEW",
            "NEW", "NEW", "CONFIRMED",
        ]

        # Фиксированные пары (client_idx, service_idx) для стабильности
        pairs = [
            (0, 0), (1, 2), (2, 4), (3, 6), (4, 8),
            (5, 10), (6, 12), (7, 14), (8, 16), (9, 18),
            (10, 1), (11, 3), (12, 5), (13, 7), (14, 9),
        ]

        created_count = 0
        skipped_count = 0

        for i, (client_idx, svc_idx) in enumerate(pairs):
            client = clients[client_idx % len(clients)]
            service = services[svc_idx % len(services)]
            scheduled_at = now + timedelta(days=schedule_offsets[i], hours=10)
            status = statuses[i]

            # Идемпотентность: одно бронирование на пару (клиент, услуга)
            exists = Booking.objects.filter(
                user=client,
                service=service,
            ).exists()

            if exists:
                skipped_count += 1
                continue

            booking = Booking.objects.create(
                user=client,
                service=service,
                status=status,
                scheduled_at=scheduled_at,
            )

            # Добавляем 1-2 позиции из ServiceItem к бронированию
            items = list(service.items.filter(is_active=True)[:2])
            for si in items:
                BookingItem.objects.create(
                    booking=booking,
                    service_item=si,
                    quantity=1,
                    price=si.price,
                )

            created_count += 1

        self.stdout.write(
            f"  Бронирования: создано {created_count}, пропущено (уже есть) {skipped_count}"
        )
