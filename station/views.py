from datetime import datetime
from re import A
from django.forms import ValidationError
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
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
)
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q


class StationViewSet(viewsets.ModelViewSet):
    """ViewSet for Station model"""

    queryset = Station.objects.all()
    serializer_class = StationSerializer

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
        Endpoint for autocomplete station names.
        Used in the frontend search form.
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


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSearchSerializer

    def perform_create(self, serializer):
        """
        When creating a trip, call clean() before saving.
        """
        instance = serializer.save(commit=False)
        try:
            instance.clean()
            instance.save()
        except ValidationError as e:
            return Response(
                {"error": e.message_dict}, status=status.HTTP_400_BAD_REQUEST
            )

    def perform_update(self, serializer):
        """
        When updating a trip, call clean() before saving.
        """
        instance = serializer.save(commit=False)
        try:
            instance.clean()
            instance.save()
        except ValidationError as e:
            return Response(
                {"error": e.message_dict}, status=status.HTTP_400_BAD_REQUEST
            )

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
            "passengers_count", "1"
        )

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

        # Filter Trips:
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
            for t in trips_qs:
                if t.is_available_for_booking(
                    passengers_count, wagon_class=None, travel_date=search_date
                ):
                    trips_filtered.append(t)
            trips_qs = trips_filtered

        serializer = TripSearchSerializer(trips_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        """
        Shows availability of seats on the selected date and the next 4 days.
        """
        trip = self.get_object()

        date_str = request.query_params.get("date")
        passengers_count_str = request.query_params.get(
            "passengers_count", "1"
        )

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
