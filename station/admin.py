from django.contrib import admin
from .models import Station, Route, Train


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
