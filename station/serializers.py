from datetime import timedelta
from django.db.models import F, ExpressionWrapper, fields
from django.db.models.functions import Abs, Extract
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
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

    def validate(self, data):
        """
        Полная валидация данных поездки
        """
        # Создаем временный объект для валидации
        instance = Trip(**data)
        if self.instance:
            instance.id = self.instance.id

        try:
            instance.clean()  # Вызываем Django-валидацию из модели
        except DjangoValidationError as e:
            # Преобразуем Django ValidationError в DRF ValidationError
            if hasattr(e, "message_dict"):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError(
                    {"non_field_errors": e.messages})

        return data


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
    wagon_types = serializers.SerializerMethodField()

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
            "wagon_types",
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
        Find alternative dates for the selected trip.
        We search for trips with:
        1. The same train
        2. The same route
        3. Departure time as close as possible to
        the original trip's time of day

        Returns up to 5 trips (including the current one).
        """
        passengers_count = self.context.get("passengers_count", 1)

        # Get time of day of the reference trip (hours and minutes)
        reference_hour = obj.departure_time.hour
        reference_minute = obj.departure_time.minute

        # Find trips with same train and route
        same_trip_query = Trip.objects.filter(
            route=obj.route,
            train=obj.train,
            # Include trips from yesterday and all future trips
            departure_time__gte=obj.departure_time.replace(
                hour=0, minute=0, second=0
            ) - timedelta(days=1),
        )

        # Calculate the time difference with the reference trip's time of day
        same_trip_query = same_trip_query.annotate(
            hour=Extract("departure_time", "hour"),
            minute=Extract("departure_time", "minute"),
            # Convert hours and minutes to minutes for easier comparison
            time_diff_minutes=Abs(
                ExpressionWrapper(
                    (F("hour") * 60 + F("minute"))
                    - (reference_hour * 60 + reference_minute),
                    output_field=fields.IntegerField(),
                )
            ),
        )

        # Order by:
        # 1. Time difference (to get trips at similar time of day)
        # 2. Departure time (for chronological order when times are equal)
        alternative_trips = same_trip_query.order_by(
            "time_diff_minutes", "departure_time"
        )[:5]

        result = []
        for trip_obj in alternative_trips:
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
                    # Add extra info to help frontend display the results
                    "is_current": trip_obj.id == obj.id,
                    "departure_date":
                    trip_obj.departure_time.date().isoformat(),
                    "departure_time_of_day":
                    trip_obj.departure_time.strftime("%H:%M"),
                    "time_diff_minutes":
                    getattr(trip_obj, "time_diff_minutes", 0),
                }
            )

        return result
