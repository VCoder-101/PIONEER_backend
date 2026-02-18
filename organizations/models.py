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
    name = models.CharField(max_length=255, verbose_name='Название', db_index=True)
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
        ]

    def __str__(self):
        return self.name
