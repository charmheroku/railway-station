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
            from django.core.exceptions import ValidationError

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
    Тип вагона (купе, плацкарт, сидячий и т.д.), влияет на цену
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
