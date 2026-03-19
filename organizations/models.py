from django.db import models
from django.conf import settings


class City(models.Model):
    """Города для организаций"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название', db_index=True)
    region = models.CharField(max_length=100, blank=True, verbose_name='Регион')
    country = models.CharField(max_length=100, default='Россия', verbose_name='Страна')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Organization(models.Model):
    """Организации владельцев"""
    
    ORGANIZATION_TYPE_CHOICES = [
        ('wash', 'Мойка'),
        ('tire', 'Шиномонтаж'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='Название', db_index=True)
    short_name = models.CharField(max_length=50, blank=True, verbose_name='Короткое название')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name='Владелец',
        db_index=True
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name='Город',
        db_index=True
    )
    address = models.CharField(max_length=500, blank=True, verbose_name='Адрес')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Новые поля
    organization_type = models.CharField(
        max_length=20,
        choices=ORGANIZATION_TYPE_CHOICES,
        default='wash',
        verbose_name='Тип организации',
        db_index=True
    )
    organization_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус заявки',
        db_index=True
    )
    organization_date_approved = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата одобрения'
    )
    
    # Государственные данные
    org_inn = models.CharField(max_length=12, blank=True, verbose_name='ИНН')
    org_ogrn = models.CharField(max_length=15, blank=True, verbose_name='ОГРН')
    org_kpp = models.CharField(max_length=9, blank=True, verbose_name='КПП')
    
    # Для шиномонтажа - диаметры дисков
    wheel_diameters = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Диаметры дисков',
        help_text='Массив диаметров дисков для шиномонтажа'
    )
    
    # Статистика
    count_services = models.IntegerField(default=0, verbose_name='Количество услуг')
    summary_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Итоговая стоимость'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['city', 'is_active']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['organization_status']),
            models.Index(fields=['organization_type']),
        ]

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # Автоматически устанавливаем дату одобрения при смене статуса на approved
        if self.organization_status == 'approved' and not self.organization_date_approved:
            from django.utils import timezone
            self.organization_date_approved = timezone.now()
        elif self.organization_status != 'approved':
            self.organization_date_approved = None
        super().save(*args, **kwargs)


# Импортируем модели расписания
from .availability_models import (
    OrganizationSchedule,
    OrganizationHoliday,
    ServiceAvailability
)

__all__ = [
    'City',
    'Organization',
    'OrganizationSchedule',
    'OrganizationHoliday',
    'ServiceAvailability',
]
