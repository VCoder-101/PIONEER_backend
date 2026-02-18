from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, CityViewSet

router = DefaultRouter()
router.register(r'cities', CityViewSet, basename='city')
router.register(r'', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('', include(router.urls)),
]
