from django.urls import path, include
from rest_framework import routers
from .views import (
    StationViewSet,
    RouteViewSet,
    TrainViewSet,
    WagonViewSet,
    WagonAmenityViewSet,
    WagonTypeViewSet,
)

app_name = "station"

router = routers.DefaultRouter()
router.register(r"stations", StationViewSet, basename="station")
router.register(r"routes", RouteViewSet, basename="route")
router.register(r"trains", TrainViewSet, basename="train")
router.register(r"wagons", WagonViewSet, basename="wagon")
router.register(
    r"wagon-amenities",
    WagonAmenityViewSet,
    basename="wagon-amenity",
)
router.register(
    r"wagon-types",
    WagonTypeViewSet,
    basename="wagon-type",
)

urlpatterns = [
    path("", include(router.urls)),
]
