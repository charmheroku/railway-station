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
