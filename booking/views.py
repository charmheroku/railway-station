from booking.models import Order
from booking.serializers import OrderSerializer, OrderCreateSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import PassengerType
from .serializers import PassengerTypeSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return all orders for admin users, only own orders for regular users
        """
        if self.request.user.is_staff:
            return Order.objects.all().prefetch_related(
                "tickets", "tickets__trip", "tickets__wagon"
            )
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets", "tickets__trip", "tickets__wagon"
        )

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
            with transaction.atomic():
                order = serializer.save()
                # Return the full order details
                return Response(
                    OrderSerializer(order, context={"request": request}).data,
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class PassengerTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing passenger types
    """

    queryset = PassengerType.objects.filter(is_active=True)
    serializer_class = PassengerTypeSerializer
    permission_classes = [AllowAny]  # Доступно без авторизации
    pagination_class = None  # Отключаем пагинацию для этого эндпоинта
