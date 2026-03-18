from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import UserSession

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_jwt_token(request):
    """
    Проверить валидность JWT access token и вернуть информацию о пользователе и ролях.

    Body:
    { "token": "<jwt_access_token>" }
    """
    token_str = request.data.get("token")
    if not token_str:
        return Response(
            {"valid": False, "error": "token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = AccessToken(token_str)  # проверяет подпись + exp
        user_id = token.get("user_id")
        if not user_id:
            return Response(
                {"valid": False, "error": "user_id not found in token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Проверяем session_id в токене
        session_id = token.get("session_id")
        if session_id:
            # Проверяем, что сессия активна
            try:
                session = UserSession.objects.get(id=session_id, user_id=user_id)
                if not session.is_active:
                    return Response(
                        {"valid": False, "error": "Token is expired"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except UserSession.DoesNotExist:
                return Response(
                    {"valid": False, "error": "Token is expired"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        user = User.objects.get(id=user_id)

        return Response(
            {
                "valid": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "roles": [user.role],
                    "is_active": user.is_active,
},
                "token": {
                    "user_id": str(user_id),
                    "exp": int(token["exp"]) if "exp" in token else None,
                    "iat": int(token["iat"]) if "iat" in token else None,
                },
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        return Response(
            {"valid": False, "error": "user not found"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as e:
        # сюда попадёт: истёк токен, неверная подпись, мусорная строка и т.д.
        return Response(
            {"valid": False, "error": str(e)},
            status=status.HTTP_401_UNAUTHORIZED,
        )