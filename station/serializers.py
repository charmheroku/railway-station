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
            "wagon_type",
            "amenities",
        ]


class WagonDetailSerializer(WagonSerializer):
    amenities = serializers.SerializerMethodField()
    wagon_type = serializers.CharField(
        source="wagon_type.name",
        read_only=True,
    )
    wagon_fare_multiplier = serializers.CharField(
        source="wagon_type.fare_multiplier",
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
        Full validation of trip data
        """
        instance = Trip(**data)
        if self.instance:
            instance.id = self.instance.id

        try:
            instance.clean()
        except DjangoValidationError as e:
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
    Returns basic information about the trip
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
                hour=0,
                minute=0,
                second=0,
            ),
        )

        # Calculate the time difference with the reference trip's time of day
        same_trip_query = same_trip_query.annotate(
            hour=Extract("departure_time", "hour"),
            minute=Extract("departure_time", "minute"),
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
            travel_date = trip_obj.departure_time.date()

            # Get all wagons for this trip's train
            wagons = (
                trip_obj.train.wagons.select_related("wagon_type")
                .prefetch_related("amenities")
                .all()
            )

            # Get all booked seats for this trip on this date
            booked_seats = {
                (ticket["wagon_id"], ticket["seat_number"])
                for ticket in trip_obj.tickets.filter(
                    trip__departure_time__date=travel_date
                ).values("wagon_id", "seat_number")
            }

            # Process each wagon
            wagons_data = []
            for wagon in wagons:
                # Calculate available seats in this wagon
                wagon_booked_seats = sum(
                    1 for seat in booked_seats if seat[0] == wagon.id
                )
                available_seats = wagon.seats - wagon_booked_seats

                # Calculate price for this wagon
                price_per_passenger = float(
                    trip_obj.base_price * wagon.wagon_type.fare_multiplier
                )

                wagons_data.append(
                    {
                        "wagon_id": wagon.id,
                        "wagon_number": wagon.number,
                        "wagon_type": wagon.wagon_type.name,
                        "total_seats": wagon.seats,
                        "booked_seats": wagon_booked_seats,
                        "available_seats": available_seats,
                        "has_enough_seats": (
                            available_seats >= passengers_count
                        ),
                        "price_per_passenger": price_per_passenger,
                        "total_price": price_per_passenger * passengers_count,
                        "amenities": [
                            {"id": a.id, "name": a.name}
                            for a in wagon.amenities.all()
                        ],
                    }
                )

            # Group wagons by type for summary
            wagon_types = {}
            for wagon in wagons_data:
                wtype = wagon["wagon_type"]
                if wtype not in wagon_types:
                    total_price = float(wagon["total_price"])
                    base_total = float(trip_obj.base_price * passengers_count)
                    wagon_types[wtype] = {
                        "total_seats": 0,
                        "available_seats": 0,
                        "has_enough_seats": False,
                        "fare_multiplier": total_price / base_total,
                    }
                wagon_types[wtype]["total_seats"] += wagon["total_seats"]
                wagon_types[wtype]["available_seats"] += (
                    wagon["available_seats"]
                )
                wagon_types[wtype]["has_enough_seats"] = (
                    wagon_types[wtype]["has_enough_seats"]
                    or wagon["has_enough_seats"]
                )

            result.append(
                {
                    "trip_id": trip_obj.id,
                    "departure_time": trip_obj.departure_time.isoformat(),
                    "arrival_time": trip_obj.arrival_time.isoformat(),
                    "is_available": any(w["has_enough_seats"]
                                        for w in wagons_data),
                    "wagons": wagons_data,
                    "wagon_types_summary": wagon_types,
                    "is_current": trip_obj.id == obj.id,
                    "departure_date": travel_date.isoformat(),
                    "departure_time_of_day": (
                        trip_obj.departure_time.strftime("%H:%M")
                    ),
                    "time_diff_minutes": getattr(
                        trip_obj, "time_diff_minutes", 0),
                }
            )

        return result
