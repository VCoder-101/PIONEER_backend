"""
Кастомные обработчики исключений для API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для унифицированных ответов API
    """
    # Получаем стандартный ответ от DRF
    response = exception_handler(exc, context)
    
    # Если это 401 (не авторизован)
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response({
            'error': 'Требуется авторизация',
            'detail': 'Вы не авторизованы. Пожалуйста, войдите в систему.',
            'code': 'not_authenticated'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Если это 403 (нет прав доступа)
    if isinstance(exc, PermissionDenied):
        return Response({
            'error': 'Доступ запрещен',
            'detail': str(exc) if str(exc) else 'У вас нет прав для выполнения этого действия.',
            'code': 'permission_denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Для остальных ошибок возвращаем стандартный ответ
    if response is not None:
        # Унифицируем формат ответа
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                response.data = {
                    'error': response.data.get('detail'),
                    'code': 'error'
                }
        return response
    
    # Если response None, значит это необработанное исключение
    return Response({
        'error': 'Внутренняя ошибка сервера',
        'detail': str(exc),
        'code': 'internal_error'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
