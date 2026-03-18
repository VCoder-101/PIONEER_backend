"""
API эндпоинты для авторизации и восстановления доступа через email.
Коды хранятся в Django cache с TTL 5 минут.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .email_service import email_verification_service
from .models import User, UserSession


# -----------------------------
# Helpers
# -----------------------------
def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def _validate_email_or_400(email: str):
    """Валидация email, возвращает None если ок, иначе Response"""
    if not email:
        return Response({"error": "Email обязателен"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Некорректный формат email"}, status=status.HTTP_400_BAD_REQUEST)
    return None


def _handle_send_code_result(result):
    """
    Обрабатывает результат отправки кода и возвращает Response с правильным статусом.
    
    Args:
        result: dict от email_verification_service.send_auth_code() или send_recovery_code()
    
    Returns:
        Response или None (если успешно)
    """
    if result.get("success"):
        return None
    
    # Проверяем причину ошибки
    if "time_left" in result:
        # Rate limiting - слишком частые запросы
        return Response(
            {
                "error": result.get("error"),
                "time_left": result.get("time_left")
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    elif "blocked_time" in result:
        # Email заблокирован после превышения попыток
        return Response(
            {
                "error": result.get("error"),
                "blocked_time": result.get("blocked_time")
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    else:
        # Реальная ошибка отправки email
        return Response(
            {"error": "Ошибка отправки email. Попробуйте позже."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_user_cars(user):
    """Получить список машин пользователя в кратком формате"""
    from cars.models import Car
    return list(
        Car.objects.filter(user=user).values('id', 'brand', 'license_plate', 'wheel_diameter')
    )


def _create_session_and_jwt(user: User, request, device_id: str, message: str, is_new: bool):
    """Единая логика: деактивировать старые сессии, создать новую, выдать JWT"""
    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)

    session = UserSession.objects.create(
        user=user,
        device_id=device_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        expires_at=timezone.now() + timedelta(days=30),
    )

    user.update_session(device_id, session.id)

    refresh = RefreshToken.for_user(user)
    # Добавляем session_id в payload токена для отслеживания
    refresh['session_id'] = str(session.id)
    access = refresh.access_token
    access['session_id'] = str(session.id)
    access = str(access)

    return Response(
        {
            "message": message,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_new": is_new,
                "cars": _get_user_cars(user),
            },
            "session": {"id": str(session.id), "expires_at": session.expires_at.isoformat()},
            "jwt": {"access": access, "refresh": str(refresh)},
        },
        status=status.HTTP_200_OK,
    )


# -----------------------------
# Registration (NEW)
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_register_email_code(request):
    """
    Регистрация: отправить код на email.

    Body:
    {
        "email": "user@example.com",
        "privacy_policy_accepted": true
    }

    Ошибки:
    - если email занят -> 400 "Пользователь с таким email уже существует"
    - если privacy_policy_accepted != true -> 400 "Необходимо принять политику конфиденциальности"
    """
    email = request.data.get("email", "").strip().lower()
    privacy_accepted = request.data.get("privacy_policy_accepted", False)

    err = _validate_email_or_400(email)
    if err:
        return err

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Пользователь с таким email уже существует"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not privacy_accepted:
        return Response(
            {"error": "Необходимо принять политику конфиденциальности"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = email_verification_service.send_auth_code(email)
    error_response = _handle_send_code_result(result)
    if error_response:
        return error_response

    data = {"message": "Код отправлен на email", "email": email}
    if "dev_code" in result:
        data["dev_code"] = result["dev_code"]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_register_email_code(request):
    """
    Регистрация: проверить код, создать пользователя и войти.

    Body:
    {
        "email": "user@example.com",
        "code": "4444",
        "device_id": "unique-device-identifier",
        "privacy_policy_accepted": true
    }
    """
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    device_id = request.data.get("device_id")
    privacy_accepted = request.data.get("privacy_policy_accepted", False)

    if not all([email, code, device_id]):
        return Response(
            {"error": "Необходимы: email, code, device_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = _validate_email_or_400(email)
    if err:
        return err

    # Если пользователь уже существует — регистрация запрещена
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Пользователь с таким email уже существует"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # privacy обязателен для регистрации
    if not privacy_accepted:
        return Response(
            {"error": "Необходимо принять политику конфиденциальности"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = email_verification_service.verify_code(email, code, purpose="auth")
    if not result.get("success"):
        return Response(
            {"error": result.get("error"), "attempts_left": result.get("attempts_left")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Создаём нового пользователя (email-only)
    user = User.objects.create_user(email=email, role="CLIENT")
    user.accept_privacy_policy()

    return _create_session_and_jwt(
        user=user,
        request=request,
        device_id=device_id,
        message="Регистрация успешна",
        is_new=True,
    )


# -----------------------------
# Login (Legacy)
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_email_auth_code(request):
    """
    Логин/вход: отправить код на email.

    Body:
    {
        "email": "user@example.com"
    }

    Ошибки:
    - если пользователя нет -> 400 "Пользователь не найден"
    """
    email = request.data.get("email", "").strip().lower()

    err = _validate_email_or_400(email)
    if err:
        return err

    if not User.objects.filter(email=email).exists():
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_400_BAD_REQUEST)

    result = email_verification_service.send_auth_code(email)
    error_response = _handle_send_code_result(result)
    if error_response:
        return error_response

    data = {"message": "Код отправлен на email", "email": email}
    if "dev_code" in result:
        data["dev_code"] = result["dev_code"]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_auth_code(request):
    """
    Логин/вход: проверить код и войти.

    Body:
    {
        "email": "user@example.com",
        "code": "4444",
        "device_id": "unique-device-identifier"
    }
    """
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    device_id = request.data.get("device_id")

    if not all([email, code, device_id]):
        return Response(
            {"error": "Необходимы: email, code, device_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = _validate_email_or_400(email)
    if err:
        return err

    result = email_verification_service.verify_code(email, code, purpose="auth")
    if not result.get("success"):
        return Response(
            {"error": result.get("error"), "attempts_left": result.get("attempts_left")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_400_BAD_REQUEST)

    return _create_session_and_jwt(
        user=user,
        request=request,
        device_id=device_id,
        message="Авторизация успешна",
        is_new=False,
    )


# -----------------------------
# Recovery
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_email_recovery_code(request):
    """
    Отправить код восстановления доступа на email.

    Body:
    { "email": "user@example.com" }

    Ответ:
    - всегда 200 (не раскрываем существование пользователя)
    """
    email = request.data.get("email", "").strip().lower()

    err = _validate_email_or_400(email)
    if err:
        return err

    if not User.objects.filter(email=email).exists():
        return Response(
            {
                "message": "Если пользователь с таким email существует, код восстановления отправлен",
                "email": email,
            },
            status=status.HTTP_200_OK,
        )

    result = email_verification_service.send_recovery_code(email)
    error_response = _handle_send_code_result(result)
    if error_response:
        return error_response

    data = {"message": "Код восстановления отправлен на email", "email": email}
    if "dev_code" in result:
        data["dev_code"] = result["dev_code"]
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_recovery_code(request):
    """
    Проверить код восстановления и войти.

    Body:
    { "email": "user@example.com", "code": "4444", "device_id": "..." }
    """
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    device_id = request.data.get("device_id")

    if not all([email, code, device_id]):
        return Response(
            {"error": "Необходимы: email, code, device_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = _validate_email_or_400(email)
    if err:
        return err

    result = email_verification_service.verify_code(email, code, purpose="recovery")
    if not result.get("success"):
        return Response(
            {"error": result.get("error"), "attempts_left": result.get("attempts_left")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

    return _create_session_and_jwt(
        user=user,
        request=request,
        device_id=device_id,
        message="Восстановление доступа успешно",
        is_new=False,
    )


# -----------------------------
# Logout
# -----------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Выйти из системы (деактивировать текущую сессию).

    Body:
    { "session_id": "uuid" }
    """
    session_id = request.data.get("session_id")
    if not session_id:
        return Response({"error": "session_id обязателен"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        session.deactivate()

        if str(request.user.current_session_id) == session_id:
            request.user.current_session_id = None
            request.user.current_device_id = None
            request.user.save(update_fields=["current_session_id", "current_device_id"])

        return Response({"message": "Выход выполнен"}, status=status.HTTP_200_OK)
    except UserSession.DoesNotExist:
        return Response({"error": "Сессия не найдена"}, status=status.HTTP_404_NOT_FOUND)



# -----------------------------
# Universal Auth (NEW) - Объединенная авторизация/регистрация
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_universal_auth_code(request):
    """
    Универсальная отправка кода: автоматически определяет регистрацию или вход.

    Логика:
    - Если пользователь не существует -> регистрация (требует privacy_policy_accepted)
    - Если пользователь существует и name заполнено -> вход
    - Если пользователь существует но name пустое -> завершение регистрации (требует privacy_policy_accepted)

    Body:
    {
        "email": "user@example.com",
        "privacy_policy_accepted": true  // обязательно для регистрации/завершения регистрации
    }
    """
    email = request.data.get("email", "").strip().lower()
    privacy_accepted = request.data.get("privacy_policy_accepted", False)

    err = _validate_email_or_400(email)
    if err:
        return err

    try:
        user = User.objects.get(email=email)
        # Пользователь существует
        if user.name:
            # Имя заполнено -> обычный вход
            auth_type = "login"
            message = "Код для входа отправлен на email"
        else:
            # Имя не заполнено -> завершение регистрации
            if not privacy_accepted:
                return Response(
                    {"error": "Необходимо принять политику конфиденциальности для завершения регистрации"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            auth_type = "complete_registration"
            message = "Код для завершения регистрации отправлен на email"
    except User.DoesNotExist:
        # Пользователь не существует -> регистрация
        if not privacy_accepted:
            return Response(
                {"error": "Необходимо принять политику конфиденциальности для регистрации"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        auth_type = "registration"
        message = "Код для регистрации отправлен на email"

    result = email_verification_service.send_auth_code(email)
    error_response = _handle_send_code_result(result)
    if error_response:
        return error_response

    data = {
        "message": message,
        "email": email,
        "auth_type": auth_type,  # "registration", "login", "complete_registration"
    }
    if "dev_code" in result:
        data["dev_code"] = result["dev_code"]

    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_universal_auth_code(request):
    """
    Универсальная проверка кода: автоматически выполняет регистрацию или вход.

    Body:
    {
        "email": "user@example.com",
        "code": "4444",
        "device_id": "unique-device-identifier",
        "name": "Имя пользователя",  // обязательно для регистрации/завершения регистрации
        "privacy_policy_accepted": true  // обязательно для регистрации/завершения регистрации
    }
    """
    email = request.data.get("email", "").strip().lower()
    code = request.data.get("code", "").strip()
    device_id = request.data.get("device_id")
    name = request.data.get("name", "").strip()
    privacy_accepted = request.data.get("privacy_policy_accepted", False)

    if not all([email, code, device_id]):
        return Response(
            {"error": "Необходимы: email, code, device_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = _validate_email_or_400(email)
    if err:
        return err

    # Проверяем код
    result = email_verification_service.verify_code(email, code, purpose="auth")
    if not result.get("success"):
        return Response(
            {"error": result.get("error"), "attempts_left": result.get("attempts_left")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
        # Пользователь существует
        if user.name:
            # Имя заполнено -> обычный вход
            auth_type = "login"
            message = "Авторизация успешна"
            is_new = False
        else:
            # Имя не заполнено -> завершение регистрации
            if not name:
                return Response(
                    {"error": "Необходимо указать имя для завершения регистрации"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not privacy_accepted:
                return Response(
                    {"error": "Необходимо принять политику конфиденциальности"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Завершаем регистрацию
            user.name = name
            user.save(update_fields=['name'])
            user.accept_privacy_policy()

            auth_type = "complete_registration"
            message = "Регистрация завершена успешно"
            is_new = True

    except User.DoesNotExist:
        # Пользователь не существует -> создаем нового
        if not name:
            return Response(
                {"error": "Необходимо указать имя для регистрации"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not privacy_accepted:
            return Response(
                {"error": "Необходимо принять политику конфиденциальности"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаём нового пользователя
        user = User.objects.create_user(email=email, name=name, role="CLIENT")
        user.accept_privacy_policy()

        auth_type = "registration"
        message = "Регистрация успешна"
        is_new = True

    return _create_session_and_jwt(
        user=user,
        request=request,
        device_id=device_id,
        message=message,
        is_new=is_new,
    )
