from datetime import timedelta
from decimal import Decimal

from rest_framework import serializers
from station.models import (
    Station,
    Route,
    Train,
    WagonAmenity,
    WagonType,
    Wagon,
    Trip,
)


class StationSerializer(serializers.ModelSerializer):
    """Serializer for Station model"""

    class Meta:
        model = Station
        fields = ["id", "name", "city", "address"]


class StationAutocompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["id", "name", "city"]


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""

    class Meta:
        model = Route
        fields = ("id", "origin_station", "destination_station", "distance_km")


class RouteDetailSerializer(RouteSerializer):
    """
    Returns the station name instead of ID.
    """

    origin_station = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )
    destination_station = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )


class TrainSerializer(serializers.ModelSerializer):
    """Serializer for Train model"""

    class Meta:
        model = Train
        fields = ["id", "name", "number", "train_type"]


class WagonAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = WagonAmenity
        fields = ("id", "name", "description")


class WagonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WagonType
        fields = ("id", "name", "fare_multiplier")


class WagonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wagon
        fields = [
            "id",
            "number",
            "seats",
            "train",
            "type",
            "amenities",
        ]


class WagonDetailSerializer(WagonSerializer):
    amenities = serializers.SerializerMethodField()
    wagon_type = serializers.CharField(
        source="type.name",
        read_only=True,
    )
    wagon_fare_multiplier = serializers.CharField(
        source="type.fare_multiplier",
        read_only=True,
    )
    train = TrainSerializer(read_only=True)

    class Meta:
        model = Wagon
        fields = [
            "id",
            "number",
            "seats",
            "wagon_type",
            "wagon_fare_multiplier",
            "amenities",
            "train",
        ]

    def get_amenities(self, obj):
        """
        Returns a list of amenities for the wagon.
        """
        return [
            {"id": amenity.id, "name": amenity.name}
            for amenity in obj.amenities.all()
        ]


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "base_price",
        ]

    def validate(self, attrs):
        if attrs["arrival_time"] <= attrs["departure_time"]:
            raise serializers.ValidationError(
                "Arrival time must be later than departure time."
            )
        return attrs


class TripCreateUpdateSerializer(TripSerializer):
    class Meta:
        model = Trip
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "base_price",
        ]


class TripDetailSerializer(TripSerializer):
    route = RouteDetailSerializer(read_only=True)
    train = TrainSerializer(read_only=True)
    available_seats = serializers.ReadOnlyField()
    sold_tickets = serializers.ReadOnlyField()
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "base_price",
            "available_seats",
            "sold_tickets",
        ]

    def get_departure_time(self, obj) -> str:
        return obj.departure_time.strftime("%Y-%m-%d %H:%M")

    def get_arrival_time(self, obj) -> str:
        return obj.arrival_time.strftime("%Y-%m-%d %H:%M")


class TripSearchSerializer(serializers.ModelSerializer):
    """
    Returns basic information about the trip:
    - id
    - train name and number
    - departure/arrival station
    - departure/arrival time
    - duration, number of stops
    - base price
    """

    train_name = serializers.CharField(source="train.name", read_only=True)
    train_number = serializers.CharField(source="train.number", read_only=True)

    origin_station = serializers.CharField(
        source="route.origin_station.name", read_only=True
    )
    destination_station = serializers.CharField(
        source="route.destination_station.name", read_only=True
    )

    duration_minutes = serializers.SerializerMethodField()
    stops_count = serializers.ReadOnlyField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "train_name",
            "train_number",
            "origin_station",
            "destination_station",
            "departure_time",
            "arrival_time",
            "duration_minutes",
            "stops_count",
            "base_price",
        ]

    def get_duration_minutes(self, obj):
        return obj.duration_in_minutes


class TripAvailabilitySerializer(serializers.ModelSerializer):

    train_name = serializers.CharField(source="train.name", read_only=True)
    train_number = serializers.CharField(source="train.number", read_only=True)
    origin_station = serializers.CharField(
        source="route.origin_station.name", read_only=True
    )
    destination_station = serializers.CharField(
        source="route.destination_station.name", read_only=True
    )

    duration_minutes = serializers.SerializerMethodField()
    stops_count = serializers.ReadOnlyField()

    wagon_types = serializers.SerializerMethodField()

    dates_availability = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "train_name",
            "train_number",
            "origin_station",
            "destination_station",
            "departure_time",
            "arrival_time",
            "duration_minutes",
            "stops_count",
            "base_price",
            "wagon_types",
            "dates_availability",
        ]

    def get_duration_minutes(self, obj):
        return obj.duration_in_minutes

    def get_wagon_types(self, obj):
        """
        Returns all unique wagon types for this train,
        so that the frontend can understand what classes exist.
        """
        wagon_types_qs = WagonType.objects.filter(
            wagons__train=obj.train).distinct()
        return [
            {
                "id": wt.id,
                "name": wt.name,
                "fare_multiplier": str(wt.fare_multiplier),
            }
            for wt in wagon_types_qs
        ]

    def get_dates_availability(self, obj):
        """
        We search in the DB for up to 5 real Trips (including the current one),
        which go on the same route and train, and not earlier than today's
        departure_time.
        """

        passengers_count = self.context.get("passengers_count", 1)

        future_trips = Trip.objects.filter(
            route=obj.route,
            train=obj.train,
            departure_time__gte=obj.departure_time,
        ).order_by("departure_time")[:5]

        result = []
        for trip_obj in future_trips:
            class_stats = trip_obj.get_available_seats_by_class(
                travel_date=trip_obj.departure_time.date()
            )

            is_available = any(
                info["available_seats"] >= passengers_count
                for info in class_stats.values()
            )

            for cls_name, cls_info in class_stats.items():
                fare_mult = cls_info["fare_multiplier"]
                base_price = trip_obj.base_price
                cls_info["price_for_passengers"] = float(
                    base_price * fare_mult * passengers_count
                )
                cls_info["has_enough_seats"] = (
                    cls_info["available_seats"] >= passengers_count
                )

            result.append(
                {
                    "trip_id": trip_obj.id,
                    "departure_time": trip_obj.departure_time.isoformat(),
                    "arrival_time": trip_obj.arrival_time.isoformat(),
                    "is_available": is_available,
                    "classes": class_stats,
                }
            )

        return result
