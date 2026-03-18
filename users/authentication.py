"""
Кастомная JWT аутентификация с проверкой активности сессии.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import UserSession


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация с проверкой активности сессии.
    Инвалидирует токены, если сессия неактивна.
    """

    def get_validated_token(self, raw_token):
        """
        Валидирует токен и проверяет активность сессии.
        """
        validated_token = super().get_validated_token(raw_token)
        
        # Проверяем session_id в токене
        session_id = validated_token.get('session_id')
        if session_id:
            user_id = validated_token.get('user_id')
            try:
                session = UserSession.objects.get(id=session_id, user_id=user_id)
                if not session.is_active:
                    raise InvalidToken('Token is expired')
            except UserSession.DoesNotExist:
                raise InvalidToken('Token is expired')
        
        return validated_token
