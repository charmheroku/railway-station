from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict, Any

from booking.models import Order, Ticket
from rest_framework.exceptions import ValidationError


class OrderService:
    """
    Service for working with orders
    """

    def create_order(self, user, tickets_data: List[Dict[str, Any]]):
        """
        Create an order with tickets
        """
        with transaction.atomic():
            # Create order
            order = Order.objects.create(user=user, status="pending")

            # Create tickets
            for ticket_data in tickets_data:
                trip = ticket_data["trip"]
                wagon = ticket_data["wagon"]
                passenger_type = ticket_data.get("passenger_type")

                # Calculate price
                base_price = trip.base_price * wagon.type.fare_multiplier

                if passenger_type:
                    if passenger_type.code == "child":
                        price = base_price * 0.5  # 50% discount for children
                    elif passenger_type.code == "infant":
                        price = 0  # Free for infants
                    else:
                        price = base_price  # Full price for adults
                else:
                    price = base_price

                Ticket.objects.create(order=order, price=price, **ticket_data)

            return order

    def get_orders_for_user(self, user):
        """
        Get orders for user with optimized queries
        """
        return Order.objects.filter(user=user).prefetch_related(
            "tickets", "tickets__trip", "tickets__wagon"
        )

    def get_all_orders(self):
        """
        Get all orders with optimized queries
        """
        return Order.objects.all().prefetch_related(
            "tickets", "tickets__trip", "tickets__wagon"
        )

    def cancel_order(self, order_id: int, user) -> Order:
        """Cancel an order"""
        order = Order.objects.get(id=order_id)

        if not user.is_staff and order.user != user:
            raise PermissionError("Cannot cancel someone else's order")

        if order.status != Order.Status.PENDING:
            raise ValidationError("Only pending orders can be cancelled")

        for ticket in order.tickets.all():
            if ticket.trip.departure_time <= timezone.now() + timedelta(
                hours=24
            ):
                raise ValidationError(
                    "Cannot cancel order less than 24h before departure"
                )

        order.status = Order.Status.CANCELLED
        order.save()
        return order
