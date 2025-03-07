from django.contrib import admin
from station.models import (
    Station,
    Route,
    Train,
    WagonType,
    WagonAmenity,
    Wagon,
)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "created_at")
    search_fields = ("name", "city")
    list_filter = ("city",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("origin_station", "destination_station", "distance_km")
    search_fields = ("origin_station__name", "destination_station__name")
    list_filter = ("origin_station__city", "destination_station__city")


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "train_type")
    search_fields = ("name", "number")
    list_filter = ("train_type",)


@admin.register(WagonType)
class WagonTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "fare_multiplier")


@admin.register(WagonAmenity)
class WagonAmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Wagon)
class WagonAdmin(admin.ModelAdmin):
    list_display = ("train", "number", "type", "seats")
