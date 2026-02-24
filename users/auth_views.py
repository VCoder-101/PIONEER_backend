from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import random
import uuid

from .models import User, AuthCode, UserSession
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([AllowAny])
def send_sms_code(request):
    """
    Отправить SMS-код на номер телефона.
    
    Body:
    {
        "phone": "8 (999) 123 45 67",
        "privacy_policy_accepted": true  // обязательно при первой регистрации
    }
    """
    phone = request.data.get('phone')
    privacy_accepted = request.data.get('privacy_policy_accepted', False)
    
    if not phone:
        return Response(
            {'error': 'Номер телефона обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Очистить формат телефона (убрать пробелы, скобки)
    phone_clean = ''.join(filter(str.isdigit, phone))
    
    # Проверить существует ли пользователь
    user_exists = User.objects.filter(phone=phone_clean).exists()
    
    # Если новый пользователь - требуем согласие с политикой
    if not user_exists and not privacy_accepted:
        return Response(
            {'error': 'Необходимо принять политику конфиденциальности'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить не было ли недавних запросов (защита от спама)
    recent_code = AuthCode.objects.filter(
        phone=phone_clean,
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).first()
    
    if recent_code:
        return Response(
            {'error': 'Код уже отправлен. Подождите 1 минуту.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Деактивировать старые коды
    AuthCode.objects.filter(phone=phone_clean, is_used=False).update(is_used=True)
    
    # Генерировать 6-значный код
    code = str(random.randint(100000, 999999))
    
    # Создать запись кода
    auth_code = AuthCode.objects.create(
        phone=phone_clean,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5),  # TTL: 5 минут
        attempts_left=3
    )
    
    # TODO: Интеграция с SMS-провайдером
    # send_sms(phone_clean, f"Ваш код: {code}")
    
    # В режиме разработки возвращаем код (убрать в продакшене!)
    return Response({
        'message': 'SMS-код отправлен',
        'phone': phone_clean,
        'code_id': str(auth_code.id),
        # ТОЛЬКО ДЛЯ РАЗРАБОТКИ:
        'dev_code': code  # Убрать в продакшене!
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_sms_code(request):
    """
    Проверить SMS-код и авторизовать пользователя.
    
    Body:
    {
        "phone": "8 (999) 123 45 67",
        "code": "123456",
        "device_id": "unique-device-identifier",
        "privacy_policy_accepted": true  // для новых пользователей
    }
    """
    phone = request.data.get('phone')
    code = request.data.get('code')
    device_id = request.data.get('device_id')
    privacy_accepted = request.data.get('privacy_policy_accepted', False)
    
    if not all([phone, code, device_id]):
        return Response(
            {'error': 'Необходимы: phone, code, device_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Очистить формат
    phone_clean = ''.join(filter(str.isdigit, phone))
    
    # Найти последний активный код
    auth_code = AuthCode.objects.filter(
        phone=phone_clean,
        is_used=False,
        expires_at__gt=timezone.now()
    ).order_by('-created_at').first()
    
    if not auth_code:
        return Response(
            {'error': 'Код не найден или истёк. Запросите новый код.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить количество попыток
    if auth_code.attempts_left <= 0:
        return Response(
            {'error': 'Превышено количество попыток. Запросите новый код.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверить код
    if auth_code.code != code:
        auth_code.use_attempt()
        return Response(
            {
                'error': 'Неверный код',
                'attempts_left': auth_code.attempts_left
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Код верный - отметить как использованный
    auth_code.mark_as_used()
    
    # Получить или создать пользователя
    user, created = User.objects.get_or_create(
        phone=phone_clean,
        defaults={'role': 'CLIENT'}
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
        expires_at=timezone.now() + timedelta(days=30)  # Сессия на 30 дней
    )
    
    # Обновить текущую сессию пользователя
    user.update_session(device_id, session.id)

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    return Response({
        'message': 'Авторизация успешна',
        'user': {
            'id': str(user.id),
            'phone': user.phone,
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


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
