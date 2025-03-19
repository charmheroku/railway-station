from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

from station.models import Trip, Wagon


class Order(models.Model):
    """
    Model for order of railway tickets
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="User",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} ({self.status})"

    @property
    def total_price(self):
        """Calculate total price based on tickets in the order"""
        return sum(ticket.price for ticket in self.tickets.all())


class PassengerType(models.Model):
    """
    Model for passenger types (adult, child, infant, etc.)
    """

    code = models.CharField(max_length=20, unique=True, verbose_name=_("Code"))
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    discount_percent = models.PositiveSmallIntegerField(
        default=0, verbose_name=_("Discount percentage")
    )
    requires_document = models.BooleanField(
        default=True, verbose_name=_("Requires document")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    order = models.PositiveSmallIntegerField(
        default=0, verbose_name=_("Display order")
    )

    class Meta:
        verbose_name = _("Passenger Type")
        verbose_name_plural = _("Passenger Types")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """
    Model for passenger ticket
    """

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Trip",
    )
    wagon = models.ForeignKey(
        Wagon,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Wagon",
    )
    seat_number = models.PositiveSmallIntegerField(verbose_name="Seat number")
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Order",
    )
    passenger_type = models.ForeignKey(
        PassengerType,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name=_("Passenger type"),
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Price", blank=True
    )
    passenger_name = models.CharField(
        max_length=100, verbose_name="Passenger name", blank=True
    )
    passenger_document = models.CharField(
        max_length=50, verbose_name="Passenger document", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        unique_together = ["trip", "wagon", "seat_number"]

    def __str__(self):
        return (
            f"Ticket for {self.trip} (Wagon {self.wagon.number}, "
            f"Seat {self.seat_number})"
        )

    def clean(self):
        """
        Validate ticket data:
        1. Check that wagon belongs to the train of this trip
        2. Check that seat number is valid for this wagon
        3. Check that seat is not already taken for this trip
        """
        # Check if the wagon belongs to the train of this trip
        if self.wagon.train != self.trip.train:
            raise ValidationError(
                "The wagon does not belong to the train of this trip."
            )

        # Check if the seat number is valid for this wagon
        if self.seat_number <= 0 or self.seat_number > self.wagon.seats:
            raise ValidationError(
                f"Invalid seat number. The wagon has {self.wagon.seats} seats."
            )

        # Check if the seat is already taken for this trip
        if (
            Ticket.objects.filter(
                trip=self.trip, wagon=self.wagon, seat_number=self.seat_number
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError("This seat is already taken for this trip.")

    def save(self, *args, **kwargs) -> None:
        """
        Override saving to automatically calculate the ticket price
        (if your logic requires auto-calculation).
        """
        self.price = self.compute_price()
        super().save(*args, **kwargs)

    def compute_price(self) -> Decimal:
        """
        Calculate the ticket price based on:
        """
        base = self.trip.base_price * self.wagon.wagon_type.fare_multiplier
        if self.passenger_type.discount_percent > 0:
            discount = Decimal(f"0.{self.passenger_type.discount_percent}")
            return base * (Decimal("1") - discount)
        else:
            return base
