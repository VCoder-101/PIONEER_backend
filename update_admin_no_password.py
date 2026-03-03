"""
Скрипт для обновления существующих пользователей:
- Удаляет пароли (set_unusable_password)
- Убеждается что admin пользователь настроен правильно
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User

def update_users():
    """Обновляет всех пользователей - удаляет пароли"""
    users = User.objects.all()
    
    print(f"Найдено пользователей: {users.count()}")
    
    for user in users:
        print(f"\nОбновление пользователя: {user.email}")
        print(f"  - is_staff: {user.is_staff}")
        print(f"  - is_superuser: {user.is_superuser}")
        print(f"  - has_usable_password: {user.has_usable_password()}")
        
        # Удаляем пароль
        user.set_unusable_password()
        user.save()
        
        print(f"  ✅ Пароль удален, теперь has_usable_password: {user.has_usable_password()}")
    
    print("\n" + "="*60)
    print("✅ Все пользователи обновлены!")
    print("="*60)
    
    # Проверяем админа
    try:
        admin = User.objects.get(email='admin@pioneer.local')
        print(f"\n📧 Админ найден: {admin.email}")
        print(f"   - is_staff: {admin.is_staff}")
        print(f"   - is_superuser: {admin.is_superuser}")
        print(f"   - has_usable_password: {admin.has_usable_password()}")
        print(f"\n✅ Теперь админ может войти через email-код на /admin/login/")
    except User.DoesNotExist:
        print("\n⚠️  Админ не найден. Создайте его командой:")
        print("   python manage.py shell")
        print("   >>> from users.models import User")
        print("   >>> User.objects.create_superuser('admin@pioneer.local')")

if __name__ == '__main__':
    update_users()
