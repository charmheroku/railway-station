from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from station.serializers import TripDetailSerializer, WagonDetailSerializer
from booking.models import Ticket, Order, PassengerType
from django.db import transaction


class PassengerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerType
        fields = [
            "id",
            "code",
            "name",
            "discount_percent",
            "requires_document",
        ]


class TicketSerializer(serializers.ModelSerializer):
    passenger_type = serializers.PrimaryKeyRelatedField(
        queryset=PassengerType.objects.all(),
        error_messages={
            "does_not_exist": (
                'Passenger type with ID "{pk_value}" does not exist.'
            ),
            "incorrect_type": (
                "Passenger type must be a valid ID number, not a string."
            ),
        },
    )

    class Meta:
        model = Ticket
        fields = [
            "id",
            "trip",
            "wagon",
            "seat_number",
            "passenger_type",
            "passenger_name",
            "passenger_document",
        ]

    validators = [
        UniqueTogetherValidator(
            queryset=Ticket.objects.all(),
            fields=["trip", "wagon", "seat_number"],
            message="This seat is already taken for this trip.",
        )
    ]

    def validate(self, data):
        trip = data.get("trip")
        wagon = data.get("wagon")
        seat_number = data.get("seat_number")

        if not trip or not wagon or not seat_number:
            raise serializers.ValidationError("All fields are required")

        if wagon.train != trip.train:
            raise serializers.ValidationError("Wagon does not belong to train")

        if seat_number <= 0 or seat_number > wagon.seats:
            raise serializers.ValidationError("Invalid seat number")

        passenger_type = data.get("passenger_type")
        passenger_document = data.get("passenger_document")

        if passenger_type.requires_document and not passenger_document:
            raise serializers.ValidationError(
                {
                    "passenger_document": (
                        f"Document is required for {passenger_type.name} "
                        f"passengers"
                    )
                }
            )

        return data


class TicketDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying ticket details
    """

    trip = TripDetailSerializer(read_only=True)
    wagon = WagonDetailSerializer(read_only=True)
    passenger_type = PassengerTypeSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "trip",
            "wagon",
            "seat_number",
            "price",
            "passenger_type",
            "passenger_name",
            "passenger_document",
            "created_at",
        ]
        read_only_fields = ["price", "created_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders
    """

    tickets = TicketSerializer(many=True, required=True)

    class Meta:
        model = Order
        fields = ["tickets"]

    def validate_tickets(self, tickets_data):
        """
        Validate tickets data:
        1. Check that at least one ticket is provided
        """
        if not tickets_data:
            raise serializers.ValidationError(
                "At least one ticket is required."
            )

        return tickets_data

    def create(self, validated_data):
        """
        Create order and tickets in a single transaction
        """

        tickets_data = validated_data.pop("tickets")
        user = self.context["request"].user

        with transaction.atomic():
            # Create order
            order = Order.objects.create(user=user, status="pending")

            # Create tickets
            for ticket_data in tickets_data:
                trip = ticket_data["trip"]
                wagon = ticket_data["wagon"]
                passenger_type = ticket_data.get("passenger_type")

                # Calculate price based on trip, wagon type and passenger type
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

                # Create ticket with calculated price
                Ticket.objects.create(order=order, price=price, **ticket_data)

        return order


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying order details
    """

    tickets = TicketDetailSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
            "status",
            "total_price",
            "tickets",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
            "total_price",
        ]
