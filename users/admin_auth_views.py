"""
Кастомная авторизация для Django Admin через email-коды
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .email_service import email_verification_service
from .models import User


@never_cache
@csrf_protect
def admin_login_request_code(request):
    """
    Страница запроса кода для входа в админку
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Введите email')
            return render(request, 'admin/login_request_code.html')
        
        # Проверяем что пользователь существует и является staff
        try:
            user = User.objects.get(email=email, is_staff=True, is_active=True)
        except User.DoesNotExist:
            messages.error(request, 'Пользователь не найден или не имеет прав доступа')
            return render(request, 'admin/login_request_code.html')
        
        # Отправляем код
        result = email_verification_service.send_auth_code(email)
        
        if result['success']:
            request.session['admin_login_email'] = email
            messages.success(request, f'Код отправлен на {email}')
            return redirect('admin_login_verify_code')
        else:
            messages.error(request, 'Ошибка отправки кода')
    
    return render(request, 'admin/login_request_code.html')


@never_cache
@csrf_protect
def admin_login_verify_code(request):
    """
    Страница проверки кода для входа в админку
    """
    email = request.session.get('admin_login_email')
    
    if not email:
        return redirect('admin_login_request_code')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, 'Введите код')
            return render(request, 'admin/login_verify_code.html', {'email': email})
        
        # Проверяем код
        result = email_verification_service.verify_code(email, code, purpose='auth')
        
        if result['success']:
            # Код верный - авторизуем пользователя
            try:
                user = User.objects.get(email=email, is_staff=True, is_active=True)
                login(request, user, backend='users.backends.EmailBackend')
                del request.session['admin_login_email']
                messages.success(request, 'Вход выполнен успешно')
                return redirect('admin:index')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
        else:
            messages.error(request, result.get('error', 'Неверный код'))
            messages.info(request, f"Осталось попыток: {result.get('attempts_left', 0)}")
    
    return render(request, 'admin/login_verify_code.html', {'email': email})
