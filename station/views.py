from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from station.models import Station
from station.serializers import StationSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


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
        Endpoint for autocomplete station names.
        Used in the frontend search form.
        """
        query = request.query_params.get("query", "")
        if len(query) < 2:
            return Response([])

        stations = Station.objects.filter(name__icontains=query)[:10]
        serializer = StationSerializer(stations, many=True)
        return Response(serializer.data)
