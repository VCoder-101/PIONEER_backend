from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # Не устанавливаем пароль - авторизация только через email-коды
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Пользователь системы.
    Аутентификация ТОЛЬКО по email через код подтверждения.
    Пароли не используются!
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Администратор'),
        ('CLIENT', 'Клиент'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name='Email',
        db_index=True,
        help_text='Email для авторизации через код подтверждения'
    )
    name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Имя",
        help_text="Имя пользователя (опционально)"
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Номер телефона',
        db_index=True,
        help_text='Формат: 8 (xxx) xxx xx xx (опционально)'
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['current_session_id']),
        ]

    def __str__(self):
        return self.email
    
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
        return f"Сессия {self.user.email} - {self.device_id}"
    
    def deactivate(self):
        """Деактивировать сессию"""
        self.is_active = False
        self.save(update_fields=['is_active'])
