from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, ServiceItemViewSet

router = DefaultRouter()
router.register(r'items', ServiceItemViewSet, basename='serviceitem')
router.register(r'', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
]
