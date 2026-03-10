"""
URL patterns for the tickets app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    TicketViewSet,
    TicketMessageViewSet,
    TicketTagViewSet,
    TicketPriorityViewSet,
    TicketStatusViewSet,
)

router = DefaultRouter()
router.register(r"", TicketViewSet, basename="ticket")
router.register(r"tags", TicketTagViewSet, basename="ticket-tag")
router.register(r"priorities", TicketPriorityViewSet, basename="ticket-priority")
router.register(r"statuses", TicketStatusViewSet, basename="ticket-status")

# Nested router for ticket messages: /api/tickets/<ticket_pk>/messages/
tickets_router = nested_routers.NestedDefaultRouter(router, r"", lookup="ticket")
tickets_router.register(r"messages", TicketMessageViewSet, basename="ticket-message")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(tickets_router.urls)),
]
