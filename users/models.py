from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ADMIN', 'Администратор'),
        ('OWNER', 'Владелец организации'),
        ('CLIENT', 'Клиент'),
    ]

    email = models.EmailField(unique=True, verbose_name='Email', db_index=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='CLIENT',
        verbose_name='Роль',
        db_index=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен', db_index=True)
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Последний вход')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.email


class UserSession(models.Model):
    """Таблица для хранения сессий пользователей"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='Пользователь',
        db_index=True
    )
    session_key = models.CharField(max_length=40, unique=True, verbose_name='Ключ сессии', db_index=True)
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
            models.Index(fields=['session_key']),
            models.Index(fields=['expires_at', 'is_active']),
        ]

    def __str__(self):
        return f"Сессия {self.user.email} - {self.session_key[:8]}..."
