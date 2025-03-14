from django.urls import path, include
from booking.views import OrderViewSet, PassengerTypeViewSet
from rest_framework.routers import DefaultRouter

app_name = "booking"
router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"passenger-types", PassengerTypeViewSet, basename="passenger-types")

urlpatterns = [
    path("", include(router.urls)),
]
