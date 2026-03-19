from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, CityViewSet
from .availability_views import (
    OrganizationScheduleViewSet,
    OrganizationHolidayViewSet,
    ServiceAvailabilityViewSet,
    AvailableSlotsViewSet
)

router = DefaultRouter()
router.register(r'cities', CityViewSet, basename='city')
router.register(r'schedules', OrganizationScheduleViewSet, basename='schedule')
router.register(r'holidays', OrganizationHolidayViewSet, basename='holiday')
router.register(r'service-availability', ServiceAvailabilityViewSet, basename='service-availability')
router.register(r'available-slots', AvailableSlotsViewSet, basename='available-slots')
router.register(r'', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('', include(router.urls)),
]
