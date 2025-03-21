from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from station.models import Station, Route, Train, WagonType, Wagon, Trip
from station.serializers import TripAvailabilitySerializer
from booking.models import Ticket, Order
from booking.models import PassengerType


class TripAvailabilitySerializerTest(TestCase):
    def setUp(self):
        # Create test user
        user = get_user_model()
        self.user = user.objects.create_user(
            email="test@example.com", password="testpass"
        )

        # Create stations
        self.station1 = Station.objects.create(
            name="Kyiv", city="Kyiv", address="Address 1"
        )
        self.station2 = Station.objects.create(
            name="Lviv", city="Lviv", address="Address 2"
        )

        # Create route
        self.route = Route.objects.create(
            origin_station=self.station1,
            destination_station=self.station2,
            distance_km=550,
        )

        # Create train
        self.train = Train.objects.create(
            name="Intercity", number="123", train_type="express"
        )

        # Create wagon types
        self.lux_type = WagonType.objects.create(
            name="Lux", fare_multiplier=Decimal("2.00")
        )
        self.economy_type = WagonType.objects.create(
            name="Economy", fare_multiplier=Decimal("1.00")
        )

        # Create passenger type
        self.adult_type = PassengerType.objects.create(
            name="Adult",
            discount_percent=0,
        )

        # Create wagons
        self.lux_wagon = Wagon.objects.create(
            train=self.train,
            wagon_type=self.lux_type,
            number="1",
            seats=20,
        )
        self.economy_wagon = Wagon.objects.create(
            train=self.train,
            wagon_type=self.economy_type,
            number="2",
            seats=40,
        )

        # Create trip
        self.trip = Trip.objects.create(
            route=self.route,
            train=self.train,
            departure_time=timezone.make_aware(datetime(2025, 3, 21, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2025, 3, 21, 14, 0)),
            base_price=Decimal("100.00"),
        )

        # Create some bookings
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(
            trip=self.trip,
            wagon=self.lux_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )
        Ticket.objects.create(
            trip=self.trip,
            wagon=self.economy_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )

    def test_serializer_output(self):
        """Test the structure and content of serializer output"""
        serializer = TripAvailabilitySerializer(
            self.trip, context={"passengers_count": 1}
        )
        data = serializer.data

        self.assertEqual(data["id"], self.trip.id)
        self.assertEqual(data["train_name"], "Intercity")
        self.assertEqual(data["train_number"], "123")
        self.assertEqual(data["base_price"], "100.00")
        self.assertEqual(data["duration_minutes"], 240)

        # Check wagon types basic info
        self.assertEqual(len(data["wagon_types"]), 2)
        lux_type = next(
            wt for wt in data["wagon_types"] if wt["name"] == "Lux"
        )
        self.assertEqual(lux_type["fare_multiplier"], "2.00")

        # Check dates availability
        self.assertTrue("dates_availability" in data)
        dates = data["dates_availability"]
        self.assertEqual(len(dates), 1)  # Should have at least current date

        current_date = dates[0]
        self.assertTrue(current_date["is_available"])
        self.assertTrue(current_date["is_current"])

        # Check wagons data
        wagons = current_date["wagons"]
        self.assertEqual(len(wagons), 2)

        lux_wagon = next(w for w in wagons if w["wagon_type"] == "Lux")
        self.assertEqual(lux_wagon["total_seats"], 20)
        self.assertEqual(lux_wagon["available_seats"], 19)

    def test_serializer_with_full_wagon(self):
        """Test serializer output when a wagon is fully booked"""
        # Book all seats in Lux wagon
        order = Order.objects.create(user=self.user)
        for seat in range(2, 21):  # Start from 2 as seat 1 is already booked
            Ticket.objects.create(
                trip=self.trip,
                wagon=self.lux_wagon,
                seat_number=seat,
                order=order,
                passenger_type=self.adult_type,
            )

        serializer = TripAvailabilitySerializer(
            self.trip, context={"passengers_count": 1}
        )
        data = serializer.data

        dates = data["dates_availability"]
        current_date = dates[0]

        # Trip should still be available due to Economy wagon
        self.assertTrue(current_date["is_available"])

        # Find Lux wagon in response
        lux_wagon = next(
            w for w in current_date["wagons"] if w["wagon_type"] == "Lux"
        )
        self.assertEqual(lux_wagon["available_seats"], 0)
        self.assertFalse(lux_wagon["has_enough_seats"])
