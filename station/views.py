from datetime import datetime
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from booking.models import Ticket
from station.models import (
    Station,
    Route,
    Train,
    Wagon,
    WagonType,
    WagonAmenity,
    Trip,
)
from station.serializers import (
    StationSerializer,
    RouteSerializer,
    RouteDetailSerializer,
    TrainSerializer,
    TripSearchSerializer,
    WagonSerializer,
    WagonTypeSerializer,
    WagonAmenitySerializer,
    WagonDetailSerializer,
    TripSerializer,
    TripAvailabilitySerializer,
    TripCreateUpdateSerializer,
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from django.db.models import Q


class StationViewSet(viewsets.ModelViewSet):
    """ViewSet for Station model"""

    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="query",
                description="Searching stations(minimum 2 characters)",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={200: StationSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
    )
    def autocomplete(self, request):
        """
        Autocomplete for stations
        """
        query = request.query_params.get("query", "")
        if len(query) < 2:
            return Response([])

        stations = Station.objects.filter(name__icontains=query)[:10]
        serializer = StationSerializer(stations, many=True)
        return Response(serializer.data)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteDetailSerializer
        return RouteSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer


class WagonTypeViewSet(viewsets.ModelViewSet):
    queryset = WagonType.objects.all()
    serializer_class = WagonTypeSerializer


class WagonAmenityViewSet(viewsets.ModelViewSet):
    queryset = WagonAmenity.objects.all()
    serializer_class = WagonAmenitySerializer


class WagonViewSet(viewsets.ModelViewSet):
    queryset = Wagon.objects.all()
    serializer_class = WagonSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return WagonDetailSerializer
        return WagonSerializer


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TripCreateUpdateSerializer
        return TripSearchSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="departure_station",
                description="Departure station",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="arrival_station",
                description="Arrival station",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="date",
                description="Date",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="passengers_count",
                description="Number of passengers",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={200: TripSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        url_path="search",
    )
    def search(self, request):
        """
        Finds all trips by criteria.
        """
        origin = request.query_params.get("origin")
        destination = request.query_params.get("destination")
        date_str = request.query_params.get("date")
        passengers_count_str = request.query_params.get(
            "passengers_count", "1")

        if not origin or not destination:
            return Response(
                {"error": "Origin and destination are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            passengers_count = int(passengers_count_str)
        except ValueError:
            passengers_count = 1

        if date_str:
            try:
                search_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            search_date = datetime.now().date()

        trips_qs = Trip.objects.filter(
            Q(route__origin_station__name__icontains=origin)
            | Q(route__origin_station__city__icontains=origin),
            Q(route__destination_station__name__icontains=destination)
            | Q(route__destination_station__city__icontains=destination),
            departure_time__date=search_date,
        ).select_related(
            "train",
            "route",
            "route__origin_station",
            "route__destination_station",
        )

        if passengers_count > 0:
            trips_filtered = []
            for trip in trips_qs:
                if trip.is_available_for_booking(
                    passengers_count, wagon_class=None, travel_date=search_date
                ):
                    trips_filtered.append(trip)
            trips_qs = trips_filtered

        serializer = TripSearchSerializer(trips_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                description="Date",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="passengers_count",
                description="Number of passengers",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ],
        responses={200: TripAvailabilitySerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="availability",
        permission_classes=[permissions.AllowAny],
    )
    def availability(self, request, pk=None):
        """
        Shows availability of seats on the selected date and the next 4 days.
        """
        trip = self.get_object()

        date_str = request.query_params.get("date")
        passengers_count_str = request.query_params.get(
            "passengers_count", "1")

        try:
            passengers_count = int(passengers_count_str)
        except ValueError:
            passengers_count = 1

        if date_str:
            try:
                check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            check_date = trip.departure_time.date()

        serializer = TripAvailabilitySerializer(
            trip,
            context={
                "date": check_date,
                "passengers_count": passengers_count,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="date",
                description="Date in YYYY-MM-DD format",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of seats with availability information",
                response={
                    "type": "object",
                    "properties": {
                        "seats": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "number": {"type": "integer"},
                                    "is_available": {"type": "boolean"},
                                    "price": {"type": "number"},
                                },
                            },
                        },
                        "wagon": {"type": "object"},
                        "trip": {"type": "object"},
                    },
                },
            ),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Trip or Wagon not found"),
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"wagons/(?P<wagon_id>\d+)/seats",
        permission_classes=[permissions.AllowAny],
    )
    def wagon_seats(self, request, pk=None, wagon_id=None):
        """
        Returns information about seats in a specific wagon for a trip.
        Each seat contains its number and availability status.

        """
        try:
            trip = self.get_object()

            try:
                wagon = Wagon.objects.get(id=wagon_id, train=trip.train)
            except Wagon.DoesNotExist:
                return Response(
                    {"error":
                     f"Wagon with ID {wagon_id}  not found in this train"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            date_str = request.query_params.get("date")
            if date_str:
                try:
                    check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                check_date = trip.departure_time.date()

            booked_seats = set(
                Ticket.objects.filter(
                    trip=trip,
                    wagon=wagon,
                    trip__departure_time__date=check_date,
                ).values_list("seat_number", flat=True)
            )

            seat_data = []
            for seat_number in range(1, wagon.seats + 1):
                price = float(
                    trip.base_price * wagon.wagon_type.fare_multiplier)

                seat_data.append(
                    {
                        "number": seat_number,
                        "is_available": seat_number not in booked_seats,
                        "price": price,
                    }
                )

            wagon_data = {
                "id": wagon.id,
                "number": wagon.number,
                "type": wagon.wagon_type.name,
                "total_seats": wagon.seats,
                "amenities": [
                    {"id": a.id, "name": a.name} for a in wagon.amenities.all()
                ],
            }

            trip_data = {
                "id": trip.id,
                "origin": trip.route.origin_station.name,
                "destination": trip.route.destination_station.name,
                "departure_time": trip.departure_time.isoformat(),
                "arrival_time": trip.arrival_time.isoformat(),
            }

            return Response(
                {
                    "seats": seat_data,
                    "wagon": wagon_data,
                    "trip": trip_data,
                    "check_date": check_date.isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()
