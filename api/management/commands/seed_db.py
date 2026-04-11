"""
Команда заполнения базы тестовыми данными.
Идемпотентна — повторный запуск не дублирует записи.

Создаёт:
  - 1 город (Самара)
  - 20 организаций с владельцами:
    * 5 только мойки (organization_type='wash') — только услуга «Мойка»
    * 5 только шиномонтаж (organization_type='tire') — только услуга «Шиномонтаж»
    * 10 комбинированных (organization_type='wash') — обе услуги
  - 20 клиентов (роль CLIENT)
  - 30 бронирований в разных статусах и датах
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
from organizations.availability_models import OrganizationSchedule
from services.models import Service, ServiceItem

User = get_user_model()

# ---------------------------------------------------------------------------
# Справочные данные
# ---------------------------------------------------------------------------

# 5 только мойки (wash, только услуга «Мойка»)
WASH_ONLY_ORGS = [
    {
        "name": "Чистый Кузов",
        "address": "ул. Московское шоссе, 100",
        "phone": "+7 846 200-10-01",
        "email": "chistiy-kuzov@samara.local",
        "description": "Профессиональная мойка и полировка кузова любой сложности.",
        "organization_type": "wash",
    },
    {
        "name": "АвтоБлеск",
        "address": "ул. Ново-Садовая, 265",
        "phone": "+7 846 200-10-02",
        "email": "avtoblsk@samara.local",
        "description": "Ручная и автоматическая мойка, химчистка салона.",
        "organization_type": "wash",
    },
    {
        "name": "Мойка на Московском",
        "address": "Московское шоссе, 332",
        "phone": "+7 846 200-10-04",
        "email": "moyka-msk@samara.local",
        "description": "Быстрая мойка рядом с выездом на трассу М5.",
        "organization_type": "wash",
    },
    {
        "name": "АвтоМойка Престиж",
        "address": "ул. Победы, 78",
        "phone": "+7 846 200-10-05",
        "email": "prestige-auto@samara.local",
        "description": "Премиальный сервис: детейлинг, защитные покрытия.",
        "organization_type": "wash",
    },
    {
        "name": "Экспресс Мойка",
        "address": "ул. Советской Армии, 185",
        "phone": "+7 846 200-10-07",
        "email": "express-moyka@samara.local",
        "description": "Мойка за 20 минут — без записи, всегда свободно.",
        "organization_type": "wash",
    },
]

# 5 только шиномонтаж (tire, только услуга «Шиномонтаж»)
TIRE_ONLY_ORGS = [
    {
        "name": "Шин-Сервис Плюс",
        "address": "пр. Кирова, 45",
        "phone": "+7 846 200-10-03",
        "email": "shin-service@samara.local",
        "description": "Шиномонтаж, балансировка, сезонное хранение шин.",
        "organization_type": "tire",
    },
    {
        "name": "Колесо",
        "address": "ул. Авроры, 110",
        "phone": "+7 846 200-10-06",
        "email": "koleso-samara@samara.local",
        "description": "Полный спектр шиномонтажных работ, правка дисков.",
        "organization_type": "tire",
    },
    {
        "name": "Шинный Мастер",
        "address": "пр. Металлургов, 68",
        "phone": "+7 846 200-10-09",
        "email": "shin-master@samara.local",
        "description": "Специализируемся на грузовых и легковых шинах.",
        "organization_type": "tire",
    },
    {
        "name": "Диск-Центр",
        "address": "ул. Мичурина, 23",
        "phone": "+7 846 200-10-11",
        "email": "disk-centr@samara.local",
        "description": "Шиномонтаж и правка литых дисков любой сложности.",
        "organization_type": "tire",
    },
    {
        "name": "ШинСтоп",
        "address": "ул. Луначарского, 3",
        "phone": "+7 846 200-10-12",
        "email": "shinstop@samara.local",
        "description": "Быстрый шиномонтаж 24/7, сезонное хранение.",
        "organization_type": "tire",
    },
]

# 10 комбинированных (wash, обе услуги — «Мойка» и «Шиномонтаж»)
COMBINED_ORGS = [
    {
        "name": "АвтоСервис Маяк",
        "address": "ул. Стара-Загора, 52",
        "phone": "+7 846 200-10-08",
        "email": "mayak-auto@samara.local",
        "description": "Мойка, шиномонтаж и мелкий ремонт в одном месте.",
        "organization_type": "wash",
    },
    {
        "name": "Кристалл Авто",
        "address": "ул. Промышленности, 302",
        "phone": "+7 846 200-10-10",
        "email": "kristall-avto@samara.local",
        "description": "Мойка, полировка, нанесение керамики.",
        "organization_type": "wash",
    },
    {
        "name": "Авто Оазис",
        "address": "ул. Дачная, 17",
        "phone": "+7 846 200-10-13",
        "email": "oasis@samara.local",
        "description": "Комплексный уход за авто: мойка и шиномонтаж.",
        "organization_type": "wash",
    },
    {
        "name": "СамараАвтоСпа",
        "address": "ул. Антонова-Овсеенко, 44",
        "phone": "+7 846 200-10-14",
        "email": "autospa@samara.local",
        "description": "Автоспа полного цикла с шиномонтажом.",
        "organization_type": "wash",
    },
    {
        "name": "Формула Чистоты",
        "address": "пр. Ленина, 1",
        "phone": "+7 846 200-10-15",
        "email": "formula@samara.local",
        "description": "Мойка и шиномонтаж у ж/д вокзала.",
        "organization_type": "wash",
    },
    {
        "name": "Pit-Stop Самара",
        "address": "ул. Революционная, 70",
        "phone": "+7 846 200-10-16",
        "email": "pitstop@samara.local",
        "description": "Быстрый сервис: мойка + шиномонтаж за час.",
        "organization_type": "wash",
    },
    {
        "name": "АвтоДом",
        "address": "ул. Гагарина, 155",
        "phone": "+7 846 200-10-17",
        "email": "avtodom@samara.local",
        "description": "Мойка, шиномонтаж, детейлинг под одной крышей.",
        "organization_type": "wash",
    },
    {
        "name": "Волга-Сервис",
        "address": "Волжское шоссе, 42",
        "phone": "+7 846 200-10-18",
        "email": "volga-service@samara.local",
        "description": "Комплексный сервис на Волжском шоссе.",
        "organization_type": "wash",
    },
    {
        "name": "МойШин",
        "address": "ул. Полевая, 80",
        "phone": "+7 846 200-10-19",
        "email": "moyshin@samara.local",
        "description": "Мойка и шины — всё что нужно автомобилю.",
        "organization_type": "wash",
    },
    {
        "name": "КомплексАвто",
        "address": "ул. Ерошевского, 20",
        "phone": "+7 846 200-10-20",
        "email": "komplexavto@samara.local",
        "description": "Полный спектр: мойка, шиномонтаж, полировка.",
        "organization_type": "wash",
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

        # 2. Организации + владельцы (20 штук)
        orgs = self._seed_organizations(city)

        # 2.5. Расписание организаций
        self._seed_schedules(orgs)

        # 3. Услуги и позиции (в зависимости от типа организации)
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
        all_org_data = WASH_ONLY_ORGS + TIRE_ONLY_ORGS + COMBINED_ORGS
        orgs = []
        for idx, data in enumerate(all_org_data, start=1):
            # Владелец организации
            owner_email = f"org{idx:02d}@pioneer.local"
            owner, owner_created = User.objects.get_or_create(
                email=owner_email,
                defaults={
                    "name": f"Владелец {data['name']}",
                    "role": "CLIENT",
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
                    "organization_type": data["organization_type"],
                    "is_active": True,
                    "organization_status": "approved",
                },
            )

            # Обновляем существующие организации: тип и статус
            updated_fields = []
            if org.organization_type != data["organization_type"]:
                org.organization_type = data["organization_type"]
                updated_fields.append("organization_type")
            if org.organization_status != "approved":
                org.organization_status = "approved"
                updated_fields.extend(["organization_status", "organization_date_approved"])
            if updated_fields:
                org.save(update_fields=updated_fields)

            status = "создана" if org_created else "уже существует"
            self.stdout.write(f"  Организация «{org.name}» ({data['organization_type']}) — {status}")
            orgs.append(org)

        return orgs

    def _seed_schedules(self, orgs: list[Organization]) -> None:
        """
        Создаёт расписание для каждой организации:
        Пн–Пт 09:00–20:00, Сб 10:00–18:00, Вс — выходной.
        """
        from datetime import time as dt_time

        weekday_configs = [
            # (weekday, is_working_day, open_time, close_time)
            (0, True,  dt_time(9, 0), dt_time(20, 0)),   # Пн
            (1, True,  dt_time(9, 0), dt_time(20, 0)),   # Вт
            (2, True,  dt_time(9, 0), dt_time(20, 0)),   # Ср
            (3, True,  dt_time(9, 0), dt_time(20, 0)),   # Чт
            (4, True,  dt_time(9, 0), dt_time(20, 0)),   # Пт
            (5, True,  dt_time(10, 0), dt_time(18, 0)),  # Сб
            (6, False, dt_time(0, 0), dt_time(0, 0)),    # Вс — выходной
        ]

        created_count = 0
        skipped_count = 0

        for org in orgs:
            for weekday, is_working, open_t, close_t in weekday_configs:
                _, created = OrganizationSchedule.objects.get_or_create(
                    organization=org,
                    weekday=weekday,
                    defaults={
                        "is_working_day": is_working,
                        "open_time": open_t,
                        "close_time": close_t,
                        "slot_duration": 30,
                        "is_active": is_working,
                    },
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            f"  Расписание: создано {created_count}, пропущено (уже есть) {skipped_count}"
        )

    def _seed_services(self, orgs: list[Organization]) -> list[Service]:
        """
        Создаёт услуги в зависимости от типа организации:
        - wash (из WASH_ONLY_ORGS): только «Мойка»
        - tire (из TIRE_ONLY_ORGS): только «Шиномонтаж»
        - wash (из COMBINED_ORGS): обе услуги — «Мойка» и «Шиномонтаж»
        """
        factors = [0.85, 0.90, 0.95, 1.00, 1.05, 1.08, 1.10, 1.13, 1.16, 1.20]

        all_org_data = WASH_ONLY_ORGS + TIRE_ONLY_ORGS + COMBINED_ORGS
        all_services: list[Service] = []

        for idx, org in enumerate(orgs):
            factor = factors[idx % len(factors)]
            org_data = all_org_data[idx]
            is_tire_only = org_data in TIRE_ONLY_ORGS
            is_wash_only = org_data in WASH_ONLY_ORGS
            # Комбинированные — всё остальное

            if not is_tire_only:
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
            else:
                # Деактивируем «Мойка» у tire-only организаций (если осталась от старого seed)
                deactivated = Service.objects.filter(
                    organization=org, title="Мойка", is_active=True
                ).update(is_active=False)
                if deactivated:
                    self.stdout.write(f"    Деактивирована «Мойка» у {org.name} (tire-only)")

            if not is_wash_only:
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
            else:
                # Деактивируем «Шиномонтаж» у wash-only организаций (если осталась от старого seed)
                deactivated = Service.objects.filter(
                    organization=org, title="Шиномонтаж", is_active=True
                ).update(is_active=False)
                if deactivated:
                    self.stdout.write(f"    Деактивирована «Шиномонтаж» у {org.name} (wash-only)")

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
        Создаёт 30 бронирований с разными статусами и датами.
        Идемпотентность: пропускаем, если бронирование
        (user, service) уже существует.
        """
        now = timezone.now()

        # Заранее определённые смещения в днях (отрицательные — прошлое)
        schedule_offsets = [
            -30, -21, -14, -10, -7, -5, -3, -2, -1, 0,
            1, 2, 5, 10, 20, -25, -18, -12, -8, -4,
            -1, 0, 3, 7, 14, -6, -3, 1, 4, 8,
        ]
        statuses = [
            "DONE", "DONE", "DONE", "DONE", "DONE",
            "CANCELLED", "CANCELLED", "CONFIRMED", "CONFIRMED", "NEW",
            "CONFIRMED", "NEW", "NEW", "NEW", "CONFIRMED",
            "DONE", "DONE", "CANCELLED", "CONFIRMED", "NEW",
            "NEW", "CONFIRMED", "NEW", "CONFIRMED", "NEW",
            "DONE", "CANCELLED", "NEW", "CONFIRMED", "NEW",
        ]

        # Фиксированные пары (client_idx, service_idx) для стабильности
        pairs = [
            (0, 0), (1, 2), (2, 4), (3, 6), (4, 8),
            (5, 10), (6, 12), (7, 14), (8, 16), (9, 18),
            (10, 1), (11, 3), (12, 5), (13, 7), (14, 9),
            (15, 11), (16, 13), (17, 15), (18, 17), (19, 19),
            (0, 3), (1, 5), (2, 7), (3, 9), (4, 11),
            (5, 13), (6, 15), (7, 17), (8, 19), (9, 1),
        ]

        created_count = 0
        skipped_count = 0

        for i, (client_idx, svc_idx) in enumerate(pairs):
            client = clients[client_idx % len(clients)]
            service = services[svc_idx % len(services)]
            scheduled_at = now + timedelta(days=schedule_offsets[i], hours=10)
            booking_status = statuses[i]

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
                status=booking_status,
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
