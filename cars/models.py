import uuid
from django.db import models
from django.conf import settings


class Car(models.Model):
    """
    Автомобиль пользователя.
    Один пользователь может иметь несколько автомобилей.
    Госномер уникален в рамках системы.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cars',
        verbose_name='Владелец',
        db_index=True
    )
    brand = models.CharField(
        max_length=100,
        verbose_name='Марка',
        help_text='Марка автомобиля, например: Toyota, BMW, Lada'
    )
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Госномер',
        db_index=True,
        help_text='Государственный регистрационный номер'
    )
    wheel_diameter = models.PositiveIntegerField(
        verbose_name='Диаметр шины',
        help_text='Диаметр диска в дюймах (число без R), например: 15, 16, 17'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['license_plate']),
        ]

    def __str__(self):
        return f"{self.brand} {self.license_plate} ({self.user.email})"
