"""
Views for ticket management.
"""
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrAgent, IsAgent
from .models import (
    Ticket, TicketMessage, TicketAttachment,
    TicketTag, TicketPriority, TicketStatus,
)
from .serializers import (
    TicketListSerializer, TicketDetailSerializer, TicketCreateSerializer,
    TicketMessageSerializer, TicketAttachmentSerializer,
    TicketTagSerializer, TicketPrioritySerializer, TicketStatusSerializer,
    TicketAssignSerializer,
)
from .services import TicketService


class TicketViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for support tickets.
    Customers see their own tickets; agents see assigned + unassigned;
    admins see all.
    """

    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "priority", "assigned_agent", "channel", "is_escalated"]
    search_fields = ["ticket_number", "subject", "description"]
    ordering_fields = ["created_at", "updated_at", "priority__level"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        if self.action in ("list", "my_tickets", "unassigned"):
            return TicketListSerializer
        return TicketDetailSerializer

    def get_queryset(self):
        return TicketService.get_filtered_tickets(self.request.user)

    def perform_create(self, serializer):
        ticket = serializer.save()
        TicketService.apply_sla_policy(ticket)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def assign(self, request, pk=None):
        """Assign ticket to an agent and/or team."""
        ticket = self.get_object()
        serializer = TicketAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ticket = TicketService.assign_ticket(
                ticket,
                agent_id=serializer.validated_data.get("assigned_agent"),
                team_id=serializer.validated_data.get("assigned_team"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def close(self, request, pk=None):
        """Close a ticket."""
        ticket = self.get_object()
        ticket = TicketService.close_ticket(ticket, resolved_by=request.user)
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def escalate(self, request, pk=None):
        """Mark a ticket as escalated."""
        ticket = self.get_object()
        ticket.is_escalated = True
        ticket.save(update_fields=["is_escalated"])
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            body="Ticket has been escalated.",
            message_type=TicketMessage.MessageType.SYSTEM,
        )
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=False, methods=["get"])
    def my_tickets(self, request):
        """Get tickets for the current user (customer or agent)."""
        if request.user.is_customer:
            qs = Ticket.objects.filter(customer=request.user)
        else:
            qs = Ticket.objects.filter(assigned_agent=request.user)
        qs = qs.select_related("priority", "status", "customer", "assigned_agent")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TicketListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def unassigned(self, request):
        """List tickets with no assigned agent."""
        qs = Ticket.objects.filter(
            assigned_agent__isnull=True
        ).select_related("priority", "status", "customer")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TicketListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def stats(self, request):
        """Return ticket count statistics."""
        base = Ticket.objects.all()
        open_statuses = TicketStatus.objects.filter(is_closed=False).values_list("id", flat=True)
        return Response({
            "total": base.count(),
            "open": base.filter(status__id__in=open_statuses).count(),
            "unassigned": base.filter(assigned_agent__isnull=True).count(),
            "escalated": base.filter(is_escalated=True).count(),
            "sla_breached": base.filter(
                Q(sla_response_breached=True) | Q(sla_resolution_breached=True)
            ).count(),
        })


class TicketMessageViewSet(viewsets.ModelViewSet):
    """Messages within a ticket thread."""

    serializer_class = TicketMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ticket_id = self.kwargs.get("ticket_pk")
        qs = TicketMessage.objects.filter(ticket_id=ticket_id).select_related("sender")
        if self.request.user.is_customer:
            qs = qs.filter(is_customer_visible=True)
        return qs

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get("ticket_pk")
        ticket = Ticket.objects.get(id=ticket_id)
        message = serializer.save(ticket=ticket, sender=self.request.user)

        # Record first agent response for SLA
        if self.request.user.is_agent or self.request.user.is_admin:
            TicketService.record_first_response(ticket)


class TicketTagViewSet(viewsets.ModelViewSet):
    """Manage ticket tags."""

    queryset = TicketTag.objects.all()
    serializer_class = TicketTagSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    search_fields = ["name"]


class TicketPriorityViewSet(viewsets.ModelViewSet):
    """Manage ticket priorities."""

    queryset = TicketPriority.objects.all()
    serializer_class = TicketPrioritySerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]


class TicketStatusViewSet(viewsets.ModelViewSet):
    """Manage ticket statuses."""

    queryset = TicketStatus.objects.all()
    serializer_class = TicketStatusSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
