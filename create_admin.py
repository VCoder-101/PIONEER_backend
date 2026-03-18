#!/usr/bin/env python
"""
Скрипт для создания администратора
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Создаем или получаем админа
admin, created = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'name': 'Administrator',
        'role': 'ADMIN',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    print(f"✅ Администратор создан: {admin.email}")
else:
    # Обновляем роль если пользователь уже существует
    if admin.role != 'ADMIN':
        admin.role = 'ADMIN'
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print(f"✅ Пользователь {admin.email} обновлен до роли ADMIN")
    else:
        print(f"ℹ️  Администратор уже существует: {admin.email}")

print(f"   ID: {admin.id}")
print(f"   Роль: {admin.role}")
print(f"   is_staff: {admin.is_staff}")
print(f"   is_superuser: {admin.is_superuser}")
