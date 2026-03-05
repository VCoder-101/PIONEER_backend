from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet
from .jwt_views import verify_jwt_token
from .email_auth_views import (
    # регистрация
    send_register_email_code,
    verify_register_email_code,
    # логин (реальные функции из email_auth_views.py)
    send_email_auth_code,
    verify_email_auth_code,
    # recovery + logout
    send_email_recovery_code,
    verify_email_recovery_code,
    logout,
)

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    # JWT
    path("auth/jwt/verify/", verify_jwt_token, name="jwt_verify"),

    # Email-регистрация
    path("auth/email/register/send-code/", send_register_email_code, name="send-email-register-code"),
    path("auth/email/register/verify-code/", verify_register_email_code, name="verify-email-register-code"),

    # Email-логин (используем существующие функции)
    path("auth/email/login/send-code/", send_email_auth_code, name="send-email-login-code"),
    path("auth/email/login/verify-code/", verify_email_auth_code, name="verify-email-login-code"),

    # Legacy (совместимость): старые пути работают как логин
    path("auth/send-code/", send_email_auth_code, name="send-email-auth-code"),
    path("auth/verify-code/", verify_email_auth_code, name="verify-email-auth-code"),

    # Recovery
    path("auth/recovery/send-code/", send_email_recovery_code, name="send-email-recovery-code"),
    path("auth/recovery/verify-code/", verify_email_recovery_code, name="verify-email-recovery-code"),

    # Logout
    path("auth/logout/", logout, name="logout"),

    # CRUD + /me
    path("", include(router.urls)),
]