import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User

try:
    admin = User.objects.get(email='admin@pioneer.local')
    print(f"Admin found: {admin.email}")
    print(f"Password hash: {admin.password[:60]}...")
    print(f"Check password 'admin123': {admin.check_password('admin123')}")
    print(f"is_staff: {admin.is_staff}")
    print(f"is_superuser: {admin.is_superuser}")
    print(f"is_active: {admin.is_active}")
except User.DoesNotExist:
    print("Admin not found!")
