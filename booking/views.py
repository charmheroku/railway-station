from booking.models import Order
from booking.serializers import OrderSerializer, OrderCreateSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import PassengerType
from .serializers import PassengerTypeSerializer
from rest_framework import mixins
from booking.services.order_service import OrderService


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing orders.
    Allows only creating new orders and viewing existing ones.
    """

    permission_classes = [IsAuthenticated]
    order_service = OrderService()

    def get_queryset(self):
        """
        Return all orders for admin users, only own orders for regular users
        """
        if self.request.user.is_staff:
            return self.order_service.get_all_orders()
        return self.order_service.get_orders_for_user(self.request.user)

    def get_serializer_class(self):
        """
        Return different serializers for different actions
        """
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    @extend_schema(
        summary="Create a new order with tickets",
        description=(
            "Create a new order with tickets. The order will be in 'pending' "
            "status."
        ),
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(description="Invalid data provided"),
        },
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new order with tickets
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = serializer.save()
            return Response(
                OrderSerializer(order, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PassengerTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing passenger types
    """

    queryset = PassengerType.objects.filter(is_active=True)
    serializer_class = PassengerTypeSerializer
