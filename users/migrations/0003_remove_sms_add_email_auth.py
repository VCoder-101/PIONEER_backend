# Generated manually
from django.db import migrations, models
import uuid


def populate_emails(apps, schema_editor):
    """Заполняем email для существующих пользователей на основе phone"""
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        if not user.email:
            # Создаем временный email на основе phone
            user.email = f"user_{user.phone}@temp.pioneer.local"
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_email_user_users_user_email_6f2530_idx'),
    ]

    operations = [
        # 1. Заполняем email для существующих пользователей
        migrations.RunPython(populate_emails, migrations.RunPython.noop),
        
        # 2. Делаем email обязательным
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(
                max_length=255,
                unique=True,
                verbose_name='Email',
                db_index=True,
                help_text='Email для авторизации и восстановления доступа'
            ),
        ),
        
        # 3. Делаем phone опциональным
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                verbose_name='Номер телефона',
                db_index=True,
                help_text='Формат: 8 (xxx) xxx xx xx (опционально)'
            ),
        ),
        
        # 4. Удаляем модель AuthCode
        migrations.DeleteModel(
            name='AuthCode',
        ),
    ]
