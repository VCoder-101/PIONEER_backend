from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_remove_sms_add_email_auth"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(
                max_length=150,
                null=True,
                blank=True,
                verbose_name="Имя",
                help_text="Имя пользователя (опционально)",
            ),
        ),
    ]