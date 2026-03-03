from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .jwt_views import verify_jwt_token
from .email_auth_views import (
    send_email_auth_code,
    verify_email_auth_code,
    send_email_recovery_code,
    verify_email_recovery_code,
    logout
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # JWT
    path("auth/jwt/verify/", verify_jwt_token, name="jwt_verify"),
    
    # Аутентификация через Email
    path('auth/send-code/', send_email_auth_code, name='send-email-auth-code'),
    path('auth/verify-code/', verify_email_auth_code, name='verify-email-auth-code'),
    
    # Восстановление доступа через Email
    path('auth/recovery/send-code/', send_email_recovery_code, name='send-email-recovery-code'),
    path('auth/recovery/verify-code/', verify_email_recovery_code, name='verify-email-recovery-code'),
    
    # Logout
    path('auth/logout/', logout, name='logout'),
    
    # CRUD пользователей
    path('', include(router.urls)),
]
