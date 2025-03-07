from rest_framework import serializers
from station.models import (
    Station,
    Route,
    Train,
    WagonAmenity,
    WagonType,
    Wagon,
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
    amenities = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
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
