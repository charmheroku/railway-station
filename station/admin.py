from django.contrib import admin
from .models import Station


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "created_at")
    search_fields = ("name", "city")
    list_filter = ("city",)
