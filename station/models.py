from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class Station(models.Model):
    """Model for railway station"""

    name = models.CharField(max_length=100, verbose_name="Name of station")
    city = models.CharField(max_length=100, verbose_name="City")
    address = models.CharField(max_length=255, verbose_name="Address")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Route(models.Model):
    """Model for route between stations"""

    origin_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes_from",
        verbose_name="Station of departure",
    )
    destination_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="routes_to",
        verbose_name="Station of arrival",
    )
    distance_km = models.PositiveIntegerField(verbose_name="Distance (km)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        unique_together = ["origin_station", "destination_station"]

    def __str__(self):
        return (
            f"{self.origin_station.name}"
            f"→ {self.destination_station.name}"
            f"({self.distance_km} км)"
        )

    def clean(self):
        """Check that departure station is not the same as arrival station"""
        if self.origin_station == self.destination_station:

            raise ValidationError(
                "Station of departure cannot be the same as station of arrival"
            )


class Train(models.Model):
    """Model for passenger train"""

    name = models.CharField(max_length=100, verbose_name="Name of train")
    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Train number",
    )
    train_type = models.CharField(
        max_length=20,
        choices=[
            ("passenger", "Passenger"),
            ("express", "Express"),
            ("suburban", "Suburban"),
        ],
        default="passenger",
        verbose_name="Train type",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Train"
        verbose_name_plural = "Trains"

    def __str__(self):
        return f"{self.name} ({self.number})"


class WagonType(models.Model):
    """
    Wagon type (coupe, economy, etc.), affects price
    """

    name = models.CharField(max_length=50, verbose_name="Name of wagon type")
    fare_multiplier = models.DecimalField(
        max_digits=3, decimal_places=2, verbose_name="Fare multiplier"
    )

    class Meta:
        verbose_name = "Wagon type"
        verbose_name_plural = "Wagon types"

    def __str__(self):
        return f"{self.name} (x{self.fare_multiplier})"


class WagonAmenity(models.Model):
    """
    Amenities in wagon (Wi-Fi, air conditioner, etc.)
    """

    name = models.CharField(max_length=100, verbose_name="Amenity name")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Wagon Amenity"
        verbose_name_plural = "Wagon Amenities"

    def __str__(self):
        return self.name


class Wagon(models.Model):
    """
    Specific wagon in train composition
    """

    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="wagons",
        verbose_name="Train",
    )
    number = models.PositiveSmallIntegerField(verbose_name="Wagon number")
    type = models.ForeignKey(
        WagonType,
        on_delete=models.PROTECT,
        related_name="wagons",
        verbose_name="Wagon type",
    )
    seats = models.PositiveSmallIntegerField(verbose_name="Number of seats")
    amenities = models.ManyToManyField(
        WagonAmenity,
        blank=True,
        related_name="wagons",
        verbose_name="Amenities",
    )

    class Meta:
        verbose_name = "Wagon"
        verbose_name_plural = "Wagons"
        unique_together = ("train", "number")

    def __str__(self):
        return f"Wagon {self.number} of Train {self.train.number}"

    def sold_seats(self, trip=None):
        """
        Count occupied seats in wagon for given trip
        """
        if trip:
            return self.tickets.filter(trip=trip).count()
        return self.tickets.count()

    def available_seats(self, trip=None):
        """
        Count available seats in wagon for given trip
        """
        if trip:
            return self.seats - self.sold_seats(trip)
        return self.seats - self.sold_seats()


class Trip(models.Model):
    """
    Trip is a specific journey
    (combination of route + train + departure/arrival time + base_price)
    """

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="Route",
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="Train",
    )
    departure_time = models.DateTimeField(verbose_name="Departure time")
    arrival_time = models.DateTimeField(verbose_name="Arrival time")
    base_price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Base price"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Trip"
        verbose_name_plural = "Trips"
        ordering = ["departure_time"]

    def __str__(self):
        dt = self.departure_time.strftime("%d.%m.%Y %H:%M")
        return (
            f"{self.route.origin_station.name} → "
            f"{self.route.destination_station.name} ({dt})"
        )

    def clean(self):
        # 1) Check that arrival_time > departure_time
        if self.arrival_time <= self.departure_time:
            raise ValidationError(
                "Arrival time must be later than departure time."
            )

        # 2) Check that there is no overlap for the same train
        overlapping = Trip.objects.filter(
            train=self.train,
            # Condition for overlap:
            # new trip (self) starts before another one ends
            # AND ends after another one starts
            departure_time__lt=self.arrival_time,
            arrival_time__gt=self.departure_time,
        ).exclude(
            id=self.id
        )  # exclude the object itself if it already exists (update)

        if overlapping.exists():
            raise ValidationError(
                f"Train {self.train} is already assigned to another trip, "
                f"overlapping in time with {self.departure_time}"
                f"– {self.arrival_time}"
            )

    @property
    def sold_tickets(self) -> int:
        return self.tickets.count()

    @property
    def available_seats(self) -> int:
        total_seats = sum(wagon.seats for wagon in self.train.wagons.all())
        return total_seats - self.sold_tickets

    @property
    def duration_in_minutes(self) -> int:
        """
        Duration of the trip in minutes.
        """
        delta = self.arrival_time - self.departure_time
        return int(delta.total_seconds() // 60)

    @property
    def total_seats(self) -> int:
        """
        Total number of seats in all wagons of this train.
        """
        return sum(wagon.seats for wagon in self.train.wagons.all())

    @property
    def available_seats_total(self) -> int:
        """
        Total number of available seats in all wagons,
        without considering the wagon class.
        """
        return self.total_seats - self.sold_tickets_count

    def get_available_seats_by_class(self, travel_date=None) -> dict:
        """
        Returns the number of available seats by each wagon type.
        """
        if travel_date is None:
            travel_date = self.departure_time.date()

        wagon_classes = {}

        for wagon in self.train.wagons.select_related("type"):
            class_name = wagon.type.name
            if class_name not in wagon_classes:
                wagon_classes[class_name] = {
                    "total_seats": 0,
                    "booked_seats": 0,
                    "available_seats": 0,
                    "fare_multiplier": wagon.type.fare_multiplier,
                }
            wagon_classes[class_name]["total_seats"] += wagon.seats

        tickets_qs = self.tickets.filter(
            trip__departure_time__date=travel_date
        )

        for ticket in tickets_qs.select_related("wagon__type"):
            class_name = ticket.wagon.type.name
            if class_name in wagon_classes:
                wagon_classes[class_name]["booked_seats"] += 1

        for class_name, class_info in wagon_classes.items():
            class_info["available_seats"] = (
                class_info["total_seats"] - class_info["booked_seats"]
            )

        return wagon_classes

    def is_available_for_booking(
        self, passengers_count=1, wagon_class=None, travel_date=None
    ) -> bool:
        """
        Check if there are enough available seats
        (in any class or in a specific class)
        for the specified number of passengers.
        """
        available_by_class = self.get_available_seats_by_class(travel_date)
        if wagon_class:
            if wagon_class not in available_by_class:
                return False
            return (
                available_by_class[wagon_class]["available_seats"]
                >= passengers_count
            )
        else:
            return any(
                class_info["available_seats"] >= passengers_count
                for class_info in available_by_class.values()
            )

    def calculate_price(
        self,
        wagon_class: str,
        passengers_count: int = 1,
    ) -> Decimal:
        """
        Calculates the price per person:
        base_price * fare_multiplier * passengers_count
        """
        wagons = self.train.wagons.filter(type__name=wagon_class)
        if not wagons.exists():
            return Decimal("0.00")

        fare_multiplier = wagons.first().type.fare_multiplier
        total_price = self.base_price * fare_multiplier * passengers_count
        return total_price.quantize(Decimal("0.01"))
