from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from organizations.models import Organization, City

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users and organizations (5 clients, 5 org users, 5 orgs)"

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) City
        city, _ = City.objects.get_or_create(
            name="Москва",
            defaults={"region": "Московская область", "country": "Россия", "is_active": True},
        )

        # 2) 5 CLIENT users
        clients = []
        for i in range(1, 6):
            phone = f"7999000001{i}"  # 79990000011..15
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={"role": "CLIENT", "is_active": True},
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
            clients.append(user)

        # 3) 5 ORGANIZATION users
        org_users = []
        for i in range(1, 6):
            phone = f"7999000002{i}"  # 79990000021..25
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={"role": "ORGANIZATION", "is_active": True},
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
            org_users.append(user)

        # 4) 5 Organizations linked to owners
        orgs = []
        for i, owner in enumerate(org_users, start=1):
            org, created = Organization.objects.get_or_create(
                name=f"Организация {i}",
                defaults={
                    "owner": owner,
                    "city": city,
                    "address": f"Улица {i}, дом {i}",
                    "phone": f"+7 999 000 00 {i:02d}",
                    "email": f"org{i}@pioneer.local",
                    "description": f"Описание организации {i}",
                    "is_active": True,
                },
            )
            # если организация уже была — убедимся, что owner правильный
            if org.owner_id != owner.id:
                org.owner = owner
                org.save(update_fields=["owner"])
            orgs.append(org)

        self.stdout.write(self.style.SUCCESS("✅ Seed done"))
        self.stdout.write("CLIENT phones: " + ", ".join([u.phone for u in clients]))
        self.stdout.write("ORG phones: " + ", ".join([u.phone for u in org_users]))
        self.stdout.write("Password for all demo users: TestPass123!")