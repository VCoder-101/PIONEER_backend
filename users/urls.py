from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .auth_views import send_sms_code, verify_sms_code, logout
from .jwt_views import verify_jwt_token
from .email_auth_views import (
    send_email_auth_code,
    verify_email_auth_code,
    send_email_recovery_code,
    verify_email_recovery_code
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Аутентификация через SMS
    path("auth/jwt/verify/", verify_jwt_token, name="jwt_verify"),
    path('auth/send-code/', send_sms_code, name='send-sms-code'),
    path('auth/verify-code/', verify_sms_code, name='verify-sms-code'),
    path('auth/logout/', logout, name='logout'),
    
    # Аутентификация через Email
    path('auth/email/send-code/', send_email_auth_code, name='send-email-auth-code'),
    path('auth/email/verify-code/', verify_email_auth_code, name='verify-email-auth-code'),
    
    # Восстановление доступа через Email
    path('auth/email/recovery/send-code/', send_email_recovery_code, name='send-email-recovery-code'),
    path('auth/email/recovery/verify-code/', verify_email_recovery_code, name='verify-email-recovery-code'),
    
    # CRUD пользователей
    path('', include(router.urls)),
]
