#!/usr/bin/env python
"""
Тест endpoint send-code
"""
import os
import django
import requests

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

def test_send_code():
    url = "http://127.0.0.1:8000/api/users/auth/send-code/"
    data = {
        "email": "test@example.com",
        "privacy_policy_accepted": True
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("\n❌ Получена ошибка 401 - проблема с авторизацией")
            print("Возможные причины:")
            print("1. Middleware блокирует запрос")
            print("2. Неправильный URL")
            print("3. Проблема с настройками DRF")
        elif response.status_code == 200:
            print("\n✅ Запрос успешен")
        else:
            print(f"\n⚠️ Неожиданный статус код: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print("Убедитесь, что сервер запущен: python manage.py runserver")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    test_send_code()