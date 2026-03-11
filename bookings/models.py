from django.db import models
from django.conf import settings


class Booking(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новая'),
        ('CONFIRMED', 'Подтверждена'),
        ('CANCELLED', 'Отменена'),
        ('DONE', 'Завершена'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Клиент',
        db_index=True
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Услуга',
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name='Статус',
        db_index=True
    )
    scheduled_at = models.DateTimeField(verbose_name='Запланировано на', db_index=True)
    car_model = models.CharField(max_length=100, blank=True, verbose_name='Модель автомобиля')
    wheel_diameter = models.IntegerField(null=True, blank=True, verbose_name='Диаметр диска')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Бронь #{self.id} - {self.user.email} - {self.service.title}"


class BookingItem(models.Model):
    """Выбранные элементы услуги в бронировании"""
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Бронирование',
        db_index=True
    )
    service_item = models.ForeignKey(
        'services.ServiceItem',
        on_delete=models.CASCADE,
        related_name='booking_items',
        verbose_name='Элемент услуги',
        db_index=True
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент бронирования')

    class Meta:
        verbose_name = 'Элемент бронирования'
        verbose_name_plural = 'Элементы бронирования'
        indexes = [
            models.Index(fields=['booking']),
        ]

    def __str__(self):
        return f"{self.service_item.name} x{self.quantity}"
