from django.urls import path, include
from rest_framework import routers
from .views import StationViewSet

app_name = "station"

router = routers.DefaultRouter()
router.register(r"stations", StationViewSet, basename="station")
urlpatterns = [
    path("", include(router.urls)),
]
