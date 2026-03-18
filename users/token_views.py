"""
Кастомные view для работы с JWT токенами.
"""
from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.utils import timezone
from .models import UserSession


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    Кастомный TokenRefreshView, который:
    1. Деактивирует старую сессию
    2. Создает новую сессию
    3. Добавляет session_id в новые токены
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        device_id = request.data.get('device_id')

        if not refresh_token:
            return Response(
                {'error': 'refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Декодируем refresh token
            refresh = RefreshToken(refresh_token)
            user_id = refresh.get('user_id')
            old_session_id = refresh.get('session_id')

            # Деактивируем старую сессию, если она есть
            if old_session_id:
                UserSession.objects.filter(id=old_session_id).update(is_active=False)

            # Деактивируем все активные сессии пользователя
            UserSession.objects.filter(user_id=user_id, is_active=True).update(is_active=False)

            # Создаем новую сессию
            new_session = UserSession.objects.create(
                user_id=user_id,
                device_id=device_id,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                expires_at=timezone.now() + timedelta(days=30),
            )

            # Обновляем информацию о сессии в пользователе
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            user.update_session(device_id, new_session.id)

            # Создаем новый refresh token с новым session_id
            new_refresh = RefreshToken.for_user(user)
            new_refresh['session_id'] = str(new_session.id)
            
            # Создаем новый access token с новым session_id
            new_access = new_refresh.access_token
            new_access['session_id'] = str(new_session.id)

            return Response({
                'access': str(new_access),
                'refresh': str(new_refresh),
                'session': {
                    'id': str(new_session.id),
                    'expires_at': new_session.expires_at.isoformat()
                }
            }, status=status.HTTP_200_OK)

        except TokenError as e:
            raise InvalidToken(e.args[0])
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
