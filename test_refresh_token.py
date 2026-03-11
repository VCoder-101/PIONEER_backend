#!/usr/bin/env python
"""
Тест refresh token functionality
"""
import os
import django
import requests
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

def test_refresh_token():
    print("=== Тест Refresh Token ===")
    
    # Создаем тестового пользователя
    user, created = User.objects.get_or_create(
        email='refresh_test@example.com',
        defaults={'role': 'CLIENT', 'name': 'Refresh Test User'}
    )
    print(f"Пользователь: {user.email} ({'создан' if created else 'найден'})")
    
    # Генерируем токены
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print(f"Access token: {access_token[:50]}...")
    print(f"Refresh token: {refresh_token[:50]}...")
    
    # Тестируем refresh endpoint
    print(f"\n=== Тест refresh endpoint ===")
    
    base_url = "http://127.0.0.1:8000"
    refresh_url = f"{base_url}/api/token/refresh/"
    
    # Данные для refresh
    refresh_data = {
        "refresh": refresh_token
    }
    
    print(f"POST {refresh_url}")
    print(f"Payload: {json.dumps(refresh_data, indent=2)}")
    
    try:
        response = requests.post(
            refresh_url,
            json=refresh_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            new_access = data.get('access')
            print(f"✅ Новый access token получен: {new_access[:50]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущен. Запустите: python manage.py runserver")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестируем использование нового токена
    print(f"\n=== Тест использования access token ===")
    
    me_url = f"{base_url}/api/users/me/"
    
    try:
        response = requests.get(
            me_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        print(f"GET {me_url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Пользователь: {data.get('email')}")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_refresh_token()