from django.contrib import admin
from .models import Order, Ticket, PassengerType


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "trip",
        "wagon",
        "seat_number",
        "passenger_name",
        "passenger_document",
    )
    list_filter = ("trip", "wagon")
    search_fields = (
        "trip__name",
        "wagon__number",
        "passenger_name",
        "passenger_document",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "status")
    list_filter = ("status",)
    search_fields = ("user__username",)
    inlines = [TicketInline]


@admin.register(PassengerType)
class PassengerTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "discount_percent", "requires_document")
    search_fields = ("name",)
