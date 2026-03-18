#!/usr/bin/env python
"""
Тест поведения send-code для существующего пользователя
"""
import os
import django
import requests

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pioneer_backend.settings')
django.setup()

from users.models import User

def test_existing_user_scenarios():
    print("=== Тест поведения send-code для существующих пользователей ===\n")
    
    # Создаем тестовых пользователей
    test_email_complete = "complete_user@test.com"
    test_email_incomplete = "incomplete_user@test.com"
    
    # Удаляем если существуют
    User.objects.filter(email__in=[test_email_complete, test_email_incomplete]).delete()
    
    # 1. Создаем полностью зарегистрированного пользователя (с именем)
    complete_user = User.objects.create_user(
        email=test_email_complete,
        name="Полный Пользователь",
        role="CLIENT"
    )
    complete_user.accept_privacy_policy()
    
    # 2. Создаем незавершенного пользователя (без имени)
    incomplete_user = User.objects.create_user(
        email=test_email_incomplete,
        role="CLIENT"
        # name не указываем - остается None
    )
    incomplete_user.accept_privacy_policy()
    
    print(f"✅ Создан полный пользователь: {complete_user.email}, name='{complete_user.name}'")
    print(f"✅ Создан неполный пользователь: {incomplete_user.email}, name='{incomplete_user.name}'\n")
    
    url = "http://127.0.0.1:8000/api/users/auth/send-code/"
    
    # Тест 1: Полностью зарегистрированный пользователь
    print("=== Тест 1: Полностью зарегистрированный пользователь ===")
    data1 = {
        "email": test_email_complete,
        "privacy_policy_accepted": True  # Не обязательно для входа, но указываем
    }
    
    try:
        response1 = requests.post(url, json=data1)
        print(f"Status: {response1.status_code}")
        print(f"Response: {response1.json()}")
        
        if response1.status_code == 200:
            resp_data = response1.json()
            print(f"✅ auth_type: {resp_data.get('auth_type')}")
            print(f"✅ message: {resp_data.get('message')}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Тест 2: Незавершенная регистрация (без имени)
    print("=== Тест 2: Незавершенная регистрация (без имени) ===")
    data2 = {
        "email": test_email_incomplete,
        "privacy_policy_accepted": True  # Обязательно для завершения регистрации
    }
    
    try:
        response2 = requests.post(url, json=data2)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.json()}")
        
        if response2.status_code == 200:
            resp_data = response2.json()
            print(f"✅ auth_type: {resp_data.get('auth_type')}")
            print(f"✅ message: {resp_data.get('message')}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Тест 3: Незавершенная регистрация БЕЗ privacy_policy_accepted
    print("=== Тест 3: Незавершенная регистрация БЕЗ privacy_policy_accepted ===")
    data3 = {
        "email": test_email_incomplete,
        "privacy_policy_accepted": False  # Должна быть ошибка
    }
    
    try:
        response3 = requests.post(url, json=data3)
        print(f"Status: {response3.status_code}")
        print(f"Response: {response3.json()}")
        
        if response3.status_code == 400:
            print("✅ Правильно вернулась ошибка 400")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Тест 4: Новый пользователь (не существует)
    print("=== Тест 4: Новый пользователь (не существует) ===")
    data4 = {
        "email": "new_user@test.com",
        "privacy_policy_accepted": True
    }
    
    try:
        response4 = requests.post(url, json=data4)
        print(f"Status: {response4.status_code}")
        print(f"Response: {response4.json()}")
        
        if response4.status_code == 200:
            resp_data = response4.json()
            print(f"✅ auth_type: {resp_data.get('auth_type')}")
            print(f"✅ message: {resp_data.get('message')}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Очистка
    print("\n=== Очистка тестовых данных ===")
    User.objects.filter(email__in=[test_email_complete, test_email_incomplete, "new_user@test.com"]).delete()
    print("✅ Тестовые пользователи удалены")

if __name__ == '__main__':
    test_existing_user_scenarios()