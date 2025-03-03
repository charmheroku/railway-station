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
