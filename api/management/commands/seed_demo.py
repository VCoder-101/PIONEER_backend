from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from organizations.models import Organization, City

User = get_user_model()


class Command(BaseCommand):
    help = "Создать демо-пользователей и организации (5 клиентов, 5 владельцев, 5 организаций)"

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Город
        city, _ = City.objects.get_or_create(
            name="Москва",
            defaults={"region": "Московская область", "country": "Россия", "is_active": True},
        )

        # 2) 5 CLIENT пользователей
        clients = []
        for i in range(1, 6):
            email = f"demo_client{i}@pioneer.local"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": f"Клиент {i}", "role": "CLIENT", "is_active": True},
            )
            clients.append(user)

        # 3) 5 ORGANIZATION пользователей
        org_users = []
        for i in range(1, 6):
            email = f"demo_org{i}@pioneer.local"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": f"Владелец {i}", "role": "CLIENT", "is_active": True},
            )
            org_users.append(user)

        # 4) 5 организаций
        orgs = []
        for i, owner in enumerate(org_users, start=1):
            org, created = Organization.objects.get_or_create(
                name=f"Демо Организация {i}",
                defaults={
                    "owner": owner,
                    "city": city,
                    "address": f"Улица {i}, дом {i}",
                    "email": f"demo_org{i}@pioneer.local",
                    "description": f"Демо организация {i}",
                    "is_active": True,
                },
            )
            if org.owner_id != owner.id:
                org.owner = owner
                org.save(update_fields=["owner"])
            orgs.append(org)

        self.stdout.write(self.style.SUCCESS("✅ Seed done"))
        self.stdout.write("CLIENT emails: " + ", ".join([u.email for u in clients]))
        self.stdout.write("ORG emails: " + ", ".join([u.email for u in org_users]))
