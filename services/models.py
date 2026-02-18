from django.db import models


class Service(models.Model):
    """Услуги организаций"""
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Организация',
        db_index=True
    )
    title = models.CharField(max_length=255, verbose_name='Название', db_index=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', db_index=True)
    duration = models.IntegerField(help_text='Длительность в минутах', verbose_name='Длительность')
    is_active = models.BooleanField(default=True, verbose_name='Активен', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['is_active', 'price']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.organization.name})"


class ServiceItem(models.Model):
    """Элементы услуг (опции, дополнения)"""
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Услуга',
        db_index=True
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    is_required = models.BooleanField(default=False, verbose_name='Обязательный')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Элемент услуги'
        verbose_name_plural = 'Элементы услуг'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['service', 'is_active']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.service.title})"
