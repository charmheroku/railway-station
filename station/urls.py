from django.urls import path, include
from rest_framework import routers
from .views import StationViewSet, RouteViewSet

app_name = "station"

router = routers.DefaultRouter()
router.register(r"stations", StationViewSet, basename="station")
router.register(r"routes", RouteViewSet, basename="route")

urlpatterns = [
    path("", include(router.urls)),
]
