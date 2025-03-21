from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from station.models import Station, Route, Train, WagonType, Wagon, Trip
from booking.models import Ticket, Order
from booking.models import PassengerType


class TripModelTest(TestCase):
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
        self.departure_time = timezone.make_aware(datetime(2025, 3, 21, 10, 0))
        self.arrival_time = timezone.make_aware(datetime(2025, 3, 21, 14, 0))
        self.trip = Trip.objects.create(
            route=self.route,
            train=self.train,
            departure_time=self.departure_time,
            arrival_time=self.arrival_time,
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

    def test_clean_validation(self):
        """Test Trip model validation"""
        # Test invalid arrival time (before departure)
        invalid_trip = Trip(
            route=self.route,
            train=self.train,
            departure_time=self.departure_time,
            arrival_time=self.departure_time - timedelta(hours=1),
            base_price=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            invalid_trip.clean()

        # Test overlapping trips
        overlapping_trip = Trip(
            route=self.route,
            train=self.train,
            departure_time=self.departure_time + timedelta(hours=1),
            arrival_time=self.arrival_time + timedelta(hours=1),
            base_price=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            overlapping_trip.clean()

    def test_duration_in_minutes(self):
        """Test trip duration calculation"""
        self.assertEqual(self.trip.duration_in_minutes, 240)

    def test_total_seats(self):
        """Test total seats calculation"""
        self.assertEqual(self.trip.total_seats, 60)

    def test_available_seats_by_class(self):
        """Test available seats calculation by wagon class"""
        # Create a trip
        trip = Trip.objects.create(
            route=self.route,
            train=self.train,
            departure_time=timezone.make_aware(datetime(2025, 3, 21, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2025, 3, 21, 14, 0)),
            base_price=Decimal("100.00"),
        )

        # Create some bookings
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(
            trip=trip,
            wagon=self.lux_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )
        Ticket.objects.create(
            trip=trip,
            wagon=self.economy_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )

        available_seats = trip.get_available_seats_by_class()

        self.assertEqual(available_seats["Lux"]["total_seats"], 20)
        self.assertEqual(available_seats["Lux"]["booked_seats"], 1)
        self.assertEqual(available_seats["Lux"]["available_seats"], 19)

        self.assertEqual(available_seats["Economy"]["total_seats"], 40)
        self.assertEqual(available_seats["Economy"]["booked_seats"], 1)
        self.assertEqual(available_seats["Economy"]["available_seats"], 39)

    def test_is_available_for_booking(self):
        """Test booking availability check"""
        trip = Trip.objects.create(
            route=self.route,
            train=self.train,
            departure_time=timezone.make_aware(datetime(2025, 3, 21, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2025, 3, 21, 14, 0)),
            base_price=Decimal("100.00"),
        )

        # Book all seats in Lux wagon
        order = Order.objects.create(user=self.user)
        for seat in range(1, 21):
            Ticket.objects.create(
                trip=trip,
                wagon=self.lux_wagon,
                seat_number=seat,
                order=order,
                passenger_type=self.adult_type,
            )

        self.assertTrue(trip.is_available_for_booking(passengers_count=1))
        self.assertFalse(
            trip.is_available_for_booking(
                passengers_count=1,
                wagon_class="Lux",
            )
        )

    def test_calculate_price(self):
        """Test price calculation with different wagon classes"""
        # Test price calculation
        lux_price = self.trip.calculate_price(
            wagon_class="Lux",
            passengers_count=2,
        )
        self.assertEqual(lux_price, Decimal("400.00"))

        economy_price = self.trip.calculate_price(
            wagon_class="Economy",
            passengers_count=2,
        )
        self.assertEqual(economy_price, Decimal("200.00"))

        invalid_price = self.trip.calculate_price(
            wagon_class="Invalid",
            passengers_count=2,
        )
        self.assertEqual(invalid_price, Decimal("0.00"))
