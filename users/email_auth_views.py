"""
API эндпоинты для авторизации и восстановления доступа через email.
Коды хранятся в Django cache с TTL 5 минут.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import User, UserSession
from .email_service import email_verification_service
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_auth_code(request):
    """
    Отправить код авторизации на email.
    
    Body:
    {
        "email": "user@example.com",
        "privacy_policy_accepted": true  // обязательно при первой регистрации
    }
    
    Response:
    {
        "message": "Код отправлен на email",
        "email": "user@example.com",
        "dev_code": "4444"  // только в режиме разработки
    }
    """
    email = request.data.get('email', '').strip().lower()
    privacy_accepted = request.data.get('privacy_policy_accepted', False)
    
    if not email:
        return Response(
            {'error': 'Email обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Валидация email
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'Некорректный формат email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить существует ли пользователь
    user_exists = User.objects.filter(email=email).exists()
    
    # Если новый пользователь - требуем согласие с политикой
    if not user_exists and not privacy_accepted:
        return Response(
            {'error': 'Необходимо принять политику конфиденциальности'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Отправить код через email сервис
    result = email_verification_service.send_auth_code(email)
    
    if not result['success']:
        return Response(
            {'error': 'Ошибка отправки email. Попробуйте позже.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    response_data = {
        'message': 'Код отправлен на email',
        'email': email
    }
    
    # В режиме разработки возвращаем код
    if 'dev_code' in result:
        response_data['dev_code'] = result['dev_code']
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_auth_code(request):
    """
    Проверить код авторизации и войти в систему.
    
    Body:
    {
        "email": "user@example.com",
        "code": "4444",
        "device_id": "unique-device-identifier",
        "privacy_policy_accepted": true  // для новых пользователей
    }
    
    Response:
    {
        "message": "Авторизация успешна",
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "phone": null,
            "role": "CLIENT",
            "is_new": false
        },
        "session": {
            "id": "uuid",
            "expires_at": "2025-03-01T12:00:00Z"
        },
        "jwt": {
            "access": "token",
            "refresh": "token"
        }
    }
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    device_id = request.data.get('device_id')
    privacy_accepted = request.data.get('privacy_policy_accepted', False)
    
    if not all([email, code, device_id]):
        return Response(
            {'error': 'Необходимы: email, code, device_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Валидация email
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'Некорректный формат email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить код через email сервис
    result = email_verification_service.verify_code(email, code, purpose='auth')
    
    if not result['success']:
        return Response(
            {
                'error': result['error'],
                'attempts_left': result['attempts_left']
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Получить или создать пользователя
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'role': 'CLIENT',
            'phone': f'email_{email[:10]}'  # Временный phone для совместимости
        }
    )
    
    # Если новый пользователь - сохранить согласие с политикой
    if created and privacy_accepted:
        user.accept_privacy_policy()
    
    # Деактивировать все старые сессии пользователя
    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
    
    # Создать новую сессию
    session = UserSession.objects.create(
        user=user,
        device_id=device_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + timedelta(days=30)
    )
    
    # Обновить текущую сессию пользователя
    user.update_session(device_id, session.id)
    
    # Генерировать JWT токены
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    
    return Response({
        'message': 'Авторизация успешна',
        'user': {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone if not user.phone.startswith('email_') else None,
            'role': user.role,
            'is_new': created
        },
        'session': {
            'id': str(session.id),
            'expires_at': session.expires_at.isoformat()
        },
        'jwt': {
            'access': access,
            'refresh': str(refresh),
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_recovery_code(request):
    """
    Отправить код восстановления доступа на email.
    
    Body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "message": "Код восстановления отправлен на email",
        "email": "user@example.com",
        "dev_code": "4444"  // только в режиме разработки
    }
    """
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response(
            {'error': 'Email обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Валидация email
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'Некорректный формат email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить существует ли пользователь
    if not User.objects.filter(email=email).exists():
        # Не раскрываем информацию о существовании пользователя
        return Response(
            {
                'message': 'Если пользователь с таким email существует, код восстановления отправлен',
                'email': email
            },
            status=status.HTTP_200_OK
        )
    
    # Отправить код через email сервис
    result = email_verification_service.send_recovery_code(email)
    
    if not result['success']:
        return Response(
            {'error': 'Ошибка отправки email. Попробуйте позже.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    response_data = {
        'message': 'Код восстановления отправлен на email',
        'email': email
    }
    
    # В режиме разработки возвращаем код
    if 'dev_code' in result:
        response_data['dev_code'] = result['dev_code']
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_recovery_code(request):
    """
    Проверить код восстановления и войти в систему.
    
    Body:
    {
        "email": "user@example.com",
        "code": "4444",
        "device_id": "unique-device-identifier"
    }
    
    Response: аналогично verify_email_auth_code
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    device_id = request.data.get('device_id')
    
    if not all([email, code, device_id]):
        return Response(
            {'error': 'Необходимы: email, code, device_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Валидация email
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'Некорректный формат email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить код через email сервис
    result = email_verification_service.verify_code(email, code, purpose='recovery')
    
    if not result['success']:
        return Response(
            {
                'error': result['error'],
                'attempts_left': result['attempts_left']
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Найти пользователя
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Деактивировать все старые сессии пользователя
    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
    
    # Создать новую сессию
    session = UserSession.objects.create(
        user=user,
        device_id=device_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + timedelta(days=30)
    )
    
    # Обновить текущую сессию пользователя
    user.update_session(device_id, session.id)
    
    # Генерировать JWT токены
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    
    return Response({
        'message': 'Восстановление доступа успешно',
        'user': {
            'id': str(user.id),
            'email': user.email,
            'phone': user.phone if not user.phone.startswith('email_') else None,
            'role': user.role,
            'is_new': False
        },
        'session': {
            'id': str(session.id),
            'expires_at': session.expires_at.isoformat()
        },
        'jwt': {
            'access': access,
            'refresh': str(refresh),
        }
    }, status=status.HTTP_200_OK)


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Выйти из системы (деактивировать текущую сессию).
    
    Body:
    {
        "session_id": "uuid"
    }
    """
    session_id = request.data.get('session_id')
    
    if not session_id:
        return Response(
            {'error': 'session_id обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        session.deactivate()
        
        # Очистить текущую сессию у пользователя
        if str(request.user.current_session_id) == session_id:
            request.user.current_session_id = None
            request.user.current_device_id = None
            request.user.save(update_fields=['current_session_id', 'current_device_id'])
        
        return Response({'message': 'Выход выполнен'}, status=status.HTTP_200_OK)
    except UserSession.DoesNotExist:
        return Response(
            {'error': 'Сессия не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
