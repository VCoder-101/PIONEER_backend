from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, phone, **extra_fields):
        if not phone:
            raise ValueError('Номер телефона обязателен')
        user = self.model(phone=phone, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(phone, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Пользователь системы.
    Аутентификация по номеру телефона через SMS-код.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Администратор'),
        ('ORGANIZATION', 'Организация'),
        ('CLIENT', 'Клиент'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Номер телефона',
        db_index=True,
        help_text='Формат: 8 (xxx) xxx xx xx'
    )
    email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Email',
        db_index=True,
        help_text='Email для авторизации и восстановления доступа'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CLIENT',
        verbose_name='Роль',
        db_index=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен', db_index=True)
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    
    # Согласие с политикой конфиденциальности
    privacy_policy_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата принятия политики конфиденциальности'
    )
    
    # Одна активная сессия на одном устройстве
    current_device_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='ID текущего устройства'
    )
    current_session_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='ID текущей сессии'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name='Последний вход')

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['current_session_id']),
        ]

    def __str__(self):
        return self.phone
    
    def accept_privacy_policy(self):
        """Принять политику конфиденциальности"""
        self.privacy_policy_accepted_at = timezone.now()
        self.save(update_fields=['privacy_policy_accepted_at'])
    
    def update_session(self, device_id, session_id):
        """Обновить активную сессию (деактивирует предыдущую)"""
        self.current_device_id = device_id
        self.current_session_id = session_id
        self.last_login_at = timezone.now()
        self.save(update_fields=['current_device_id', 'current_session_id', 'last_login_at'])


class AuthCode(models.Model):
    """
    SMS-коды для аутентификации.
    TTL: 5 минут
    Максимум попыток: 3
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', db_index=True)
    code = models.CharField(max_length=6, verbose_name='SMS-код')
    attempts_left = models.IntegerField(default=3, verbose_name='Осталось попыток')
    is_used = models.BooleanField(default=False, verbose_name='Использован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан', db_index=True)
    expires_at = models.DateTimeField(verbose_name='Истекает', db_index=True)

    class Meta:
        verbose_name = 'SMS-код'
        verbose_name_plural = 'SMS-коды'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', 'is_used']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Код для {self.phone} - {self.code}"
    
    def is_valid(self):
        """Проверить валидность кода"""
        return (
            not self.is_used and
            self.attempts_left > 0 and
            timezone.now() < self.expires_at
        )
    
    def use_attempt(self):
        """Использовать попытку"""
        self.attempts_left -= 1
        self.save(update_fields=['attempts_left'])
    
    def mark_as_used(self):
        """Отметить как использованный"""
        self.is_used = True
        self.save(update_fields=['is_used'])


class UserSession(models.Model):
    """
    Сессии пользователей.
    Только одна активная сессия на одном устройстве.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Пользователь',
        db_index=True
    )
    device_id = models.CharField(max_length=255, verbose_name='ID устройства', db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана', db_index=True)
    expires_at = models.DateTimeField(verbose_name='Истекает', db_index=True)
    is_active = models.BooleanField(default=True, verbose_name='Активна', db_index=True)

    class Meta:
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
            models.Index(fields=['expires_at', 'is_active']),
        ]

    def __str__(self):
        return f"Сессия {self.user.phone} - {self.device_id}"
    
    def deactivate(self):
        """Деактивировать сессию"""
        self.is_active = False
        self.save(update_fields=['is_active'])
