from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from station.models import Station, Route, Train, WagonType, Wagon, Trip
from booking.models import Ticket, Order
from booking.models import PassengerType


class TripViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()

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
        self.station3 = Station.objects.create(
            name="Kharkiv", city="Kharkiv", address="Address 3"
        )

        # Create routes
        self.route1 = Route.objects.create(
            origin_station=self.station1,
            destination_station=self.station2,
            distance_km=550,
        )
        self.route2 = Route.objects.create(
            origin_station=self.station1,
            destination_station=self.station3,
            distance_km=480,
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

        # Create trips
        self.departure_time = timezone.make_aware(datetime(2025, 3, 21, 10, 0))
        self.arrival_time = timezone.make_aware(datetime(2025, 3, 21, 14, 0))

        # Kyiv -> Lviv trip
        self.trip1 = Trip.objects.create(
            route=self.route1,
            train=self.train,
            departure_time=self.departure_time,
            arrival_time=self.arrival_time,
            base_price=Decimal("100.00"),
        )

        # Kyiv -> Kharkiv trip (later)
        self.trip2 = Trip.objects.create(
            route=self.route2,
            train=self.train,
            departure_time=self.departure_time + timedelta(hours=2),
            arrival_time=self.arrival_time + timedelta(hours=2),
            base_price=Decimal("120.00"),
        )

    def test_search_trips(self):
        """Test searching for trips"""
        url = reverse("station:trip-search")

        # Search with valid parameters
        response = self.client.get(
            url,
            {
                "origin": "Kyiv",
                "destination": "Lviv",
                "date": "2025-03-21",
                "passengers_count": 2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["origin_station"], "Kyiv")
        self.assertEqual(response.data[0]["destination_station"], "Lviv")

        # Search without required parameters
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Search with invalid date format
        response = self.client.get(
            url,
            {
                "origin": "Kyiv",
                "destination": "Lviv",
                "date": "invalid-date",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trip_availability(self):
        """Test trip availability endpoint"""
        url = reverse(
            "station:trip-availability",
            kwargs={"pk": self.trip1.id},
        )

        # Test with no bookings
        response = self.client.get(
            url,
            {"date": "2025-03-21", "passengers_count": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dates = response.data["dates_availability"]
        self.assertEqual(len(dates), 1)

        current_date = dates[0]
        self.assertTrue(current_date["is_available"])

        wagons = current_date["wagons"]
        self.assertEqual(len(wagons), 2)

        # Book some seats and test again
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(
            trip=self.trip1,
            wagon=self.lux_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )

        response = self.client.get(
            url,
            {"date": "2025-03-21", "passengers_count": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dates = response.data["dates_availability"]
        current_date = dates[0]

        self.assertTrue(current_date["is_available"])

        for seat in range(2, 21):
            Ticket.objects.create(
                trip=self.trip1,
                wagon=self.lux_wagon,
                seat_number=seat,
                order=order,
                passenger_type=self.adult_type,
            )

        response = self.client.get(
            url,
            {"date": "2025-03-21", "passengers_count": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dates = response.data["dates_availability"]
        current_date = dates[0]

        self.assertTrue(current_date["is_available"])

        # Find Lux wagon in response
        lux_wagon = next(
            (w for w in current_date["wagons"] if w["wagon_type"] == "Lux")
        )
        self.assertEqual(lux_wagon["available_seats"], 0)
        self.assertFalse(lux_wagon["has_enough_seats"])

    def test_wagon_seats(self):
        """Test wagon seats endpoint"""
        url = reverse(
            "station:trip-wagon-seats",
            kwargs={"pk": self.trip1.id, "wagon_id": self.lux_wagon.id},
        )

        # Test with no bookings
        response = self.client.get(url, {"date": "2025-03-21"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["seats"]), 20)

        # Check all seats availability
        self.assertTrue(all(s["is_available"] for s in response.data["seats"]))

        order = Order.objects.create(user=self.user)
        Ticket.objects.create(
            trip=self.trip1,
            wagon=self.lux_wagon,
            seat_number=1,
            order=order,
            passenger_type=self.adult_type,
        )

        response = self.client.get(url, {"date": "2025-03-21"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        seat_1 = next(s for s in response.data["seats"] if s["number"] == 1)
        self.assertFalse(seat_1["is_available"])

        # Test with invalid wagon ID
        url = reverse(
            "station:trip-wagon-seats",
            kwargs={"pk": self.trip1.id, "wagon_id": 9999},
        )
        response = self.client.get(url, {"date": "2025-03-21"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
