from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

# Публичные пути (auth и админка)
# Всё, что начинается с /api/users/auth/ — публичное (send/verify/register/login/recovery/jwt-verify и т.д.)
EXEMPT_PREFIXES = (
    "/admin/",
    "/api/users/auth/",
)


class JWTAuthorizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        path = request.path

        # пропускаем публичные пути
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)

        # проверяем только API
        if path.startswith("/api/"):
            header = request.META.get("HTTP_AUTHORIZATION", "")
            if not header.startswith("Bearer "):
                return JsonResponse(
                    {"detail": "Authorization header missing (Bearer token required)"},
                    status=401
                )

            # если токен есть — валидируем
            try:
                user_auth_tuple = self.jwt_auth.authenticate(request)
                if user_auth_tuple is None:
                    return JsonResponse({"detail": "Invalid token"}, status=401)
                # (user, validated_token) - DRF потом всё равно проставит request.user
            except Exception as e:
                return JsonResponse({"detail": str(e)}, status=401)

        return self.get_response(request)