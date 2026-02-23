from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .auth_views import send_sms_code, verify_sms_code, logout

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Аутентификация
    path('auth/send-code/', send_sms_code, name='send-sms-code'),
    path('auth/verify-code/', verify_sms_code, name='verify-sms-code'),
    path('auth/logout/', logout, name='logout'),
    
    # CRUD пользователей
    path('', include(router.urls)),
]
