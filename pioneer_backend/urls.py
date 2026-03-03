"""
URL configuration for pioneer_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users.admin_auth_views import admin_login_request_code, admin_login_verify_code

# Переопределяем стандартный login URL для админки
admin.site.login = admin_login_request_code

urlpatterns = [
    # Кастомные маршруты для входа в админку
    path('admin/login/', admin_login_request_code, name='admin_login_request_code'),
    path('admin/login/verify/', admin_login_verify_code, name='admin_login_verify_code'),
    
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/organizations/', include('organizations.urls')),
    path('api/services/', include('services.urls')),
    path('api/bookings/', include('bookings.urls')),
]
