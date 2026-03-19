"""
Модели для управления расписанием работы организаций
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class OrganizationSchedule(models.Model):
    """
    Расписание работы организации по дням недели
    """
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Организация',
        db_index=True
    )
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name='День недели',
        db_index=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    is_working_day = models.BooleanField(
        default=True,
        verbose_name='Рабочий день'
    )
    open_time = models.TimeField(
        verbose_name='Время открытия',
        help_text='Формат: HH:MM'
    )
    close_time = models.TimeField(
        verbose_name='Время закрытия',
        help_text='Формат: HH:MM'
    )
    break_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Начало перерыва',
        help_text='Опционально'
    )
    break_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Конец перерыва',
        help_text='Опционально'
    )
    slot_duration = models.IntegerField(
        default=30,
        verbose_name='Длительность слота (минуты)',
        help_text='Минимальный интервал для записи',
        validators=[MinValueValidator(5), MaxValueValidator(240)]
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Расписание организации'
        verbose_name_plural = 'Расписания организаций'
        ordering = ['organization', 'weekday']
        unique_together = ['organization', 'weekday']
        indexes = [
            models.Index(fields=['organization', 'weekday']),
            models.Index(fields=['organization', 'is_working_day']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_weekday_display()}"


class OrganizationHoliday(models.Model):
    """
    Выходные и праздничные дни организации
    """
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='holidays',
        verbose_name='Организация',
        db_index=True
    )
    date = models.DateField(
        verbose_name='Дата',
        db_index=True
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Причина',
        help_text='Например: Новый год, технический перерыв'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Выходной день'
        verbose_name_plural = 'Выходные дни'
        ordering = ['organization', 'date']
        unique_together = ['organization', 'date']
        indexes = [
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['date', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.date}"


class ServiceAvailability(models.Model):
    """
    Настройки доступности конкретной услуги
    (переопределяет общее расписание организации)
    """
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='availability_rules',
        verbose_name='Услуга',
        db_index=True
    )
    weekday = models.IntegerField(
        choices=OrganizationSchedule.WEEKDAY_CHOICES,
        verbose_name='День недели',
        db_index=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    available_from = models.TimeField(
        verbose_name='Доступна с',
        help_text='Время начала доступности услуги'
    )
    available_to = models.TimeField(
        verbose_name='Доступна до',
        help_text='Время окончания доступности услуги'
    )
    max_bookings_per_slot = models.IntegerField(
        default=1,
        verbose_name='Макс. записей на слот',
        help_text='Количество одновременных записей',
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Доступность услуги'
        verbose_name_plural = 'Доступность услуг'
        ordering = ['service', 'weekday']
        unique_together = ['service', 'weekday']
        indexes = [
            models.Index(fields=['service', 'weekday']),
            models.Index(fields=['service', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.service.title} - {self.get_weekday_display()}"
