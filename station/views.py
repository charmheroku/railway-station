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
    WagonSerializer,
    WagonTypeSerializer,
    WagonAmenitySerializer,
    WagonDetailSerializer,
    TripSerializer,
    TripDetailSerializer,
)
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly


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


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TripDetailSerializer
        return TripSerializer
