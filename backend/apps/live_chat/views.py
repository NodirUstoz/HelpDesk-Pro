"""
REST views for live chat sessions and messages.
WebSocket communication is handled in consumers.py.
"""
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Agent
from apps.accounts.permissions import IsAdminOrAgent
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionListSerializer,
    ChatSessionDetailSerializer,
    ChatSessionCreateSerializer,
    ChatSessionRatingSerializer,
    ChatMessageSerializer,
)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    REST API for chat sessions.
    Customers can initiate chats and view their own.
    Agents see waiting + their active sessions.
    """

    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "agent", "department"]
    search_fields = ["subject", "customer__email"]
    ordering = ["-started_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ChatSessionCreateSerializer
        if self.action in ("list", "waiting", "my_chats"):
            return ChatSessionListSerializer
        return ChatSessionDetailSerializer

    def get_queryset(self):
        qs = ChatSession.objects.select_related("customer", "agent").annotate(
            message_count_val=Count("messages")
        )
        user = self.request.user

        if user.is_admin:
            return qs
        elif user.is_agent:
            return qs.filter(
                Q(agent=user) | Q(status=ChatSession.Status.WAITING)
            )
        else:
            return qs.filter(customer=user)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def waiting(self, request):
        """Return chat sessions waiting for an agent."""
        qs = ChatSession.objects.filter(
            status=ChatSession.Status.WAITING
        ).select_related("customer").order_by("started_at")
        serializer = ChatSessionListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_chats(self, request):
        """Return active chats for the current user."""
        user = request.user
        if user.is_agent or user.is_admin:
            qs = ChatSession.objects.filter(
                agent=user, status=ChatSession.Status.ACTIVE
            )
        else:
            qs = ChatSession.objects.filter(
                customer=user,
                status__in=[ChatSession.Status.WAITING, ChatSession.Status.ACTIVE],
            )
        serializer = ChatSessionListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def accept(self, request, pk=None):
        """Agent accepts a waiting chat session."""
        session = self.get_object()
        if session.status != ChatSession.Status.WAITING:
            return Response(
                {"error": "This session is not in waiting status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.agent = request.user
        session.status = ChatSession.Status.ACTIVE
        session.agent_joined_at = timezone.now()
        session.save(update_fields=["agent", "status", "agent_joined_at"])

        # Update agent chat count
        if hasattr(request.user, "agent_profile"):
            profile = request.user.agent_profile
            profile.current_chat_count += 1
            profile.save(update_fields=["current_chat_count"])

        ChatMessage.objects.create(
            session=session,
            sender=None,
            content=f"{request.user.get_full_name()} has joined the chat.",
            message_type=ChatMessage.MessageType.SYSTEM,
        )

        return Response(ChatSessionDetailSerializer(session).data)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        """End a chat session."""
        session = self.get_object()
        if session.status == ChatSession.Status.CLOSED:
            return Response(
                {"error": "This session is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.status = ChatSession.Status.CLOSED
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])

        # Update agent chat count
        if session.agent and hasattr(session.agent, "agent_profile"):
            profile = session.agent.agent_profile
            profile.current_chat_count = max(0, profile.current_chat_count - 1)
            profile.save(update_fields=["current_chat_count"])

        ChatMessage.objects.create(
            session=session,
            sender=None,
            content="Chat session has ended.",
            message_type=ChatMessage.MessageType.SYSTEM,
        )

        return Response(ChatSessionDetailSerializer(session).data)

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        """Submit a rating for a closed chat session."""
        session = self.get_object()
        if session.status != ChatSession.Status.CLOSED:
            return Response(
                {"error": "Can only rate closed sessions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ChatSessionRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session.rating = serializer.validated_data["rating"]
        session.rating_comment = serializer.validated_data.get("rating_comment", "")
        session.save(update_fields=["rating", "rating_comment"])

        return Response(ChatSessionDetailSerializer(session).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def convert_to_ticket(self, request, pk=None):
        """Convert a chat session into a support ticket."""
        from apps.tickets.models import Ticket, TicketMessage, TicketStatus

        session = self.get_object()
        if session.ticket:
            return Response(
                {"error": "This session already has an associated ticket."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_status = TicketStatus.objects.filter(is_default=True).first()
        ticket = Ticket.objects.create(
            subject=session.subject or f"Chat session {str(session.id)[:8]}",
            description=f"Converted from live chat session.",
            channel=Ticket.Channel.CHAT,
            customer=session.customer,
            assigned_agent=session.agent,
            status=default_status,
        )

        # Copy chat messages as ticket messages
        for msg in session.messages.exclude(message_type=ChatMessage.MessageType.SYSTEM):
            TicketMessage.objects.create(
                ticket=ticket,
                sender=msg.sender,
                body=msg.content,
                message_type=TicketMessage.MessageType.REPLY,
            )

        session.ticket = ticket
        session.save(update_fields=["ticket"])

        return Response({
            "ticket_id": str(ticket.id),
            "ticket_number": ticket.ticket_number,
            "message": "Chat converted to ticket successfully.",
        })

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdminOrAgent])
    def stats(self, request):
        """Chat statistics overview."""
        today = timezone.now().date()
        sessions_today = ChatSession.objects.filter(started_at__date=today)
        return Response({
            "total_today": sessions_today.count(),
            "waiting": sessions_today.filter(status=ChatSession.Status.WAITING).count(),
            "active": sessions_today.filter(status=ChatSession.Status.ACTIVE).count(),
            "closed_today": sessions_today.filter(status=ChatSession.Status.CLOSED).count(),
            "avg_rating": self._avg_rating_today(sessions_today),
        })

    def _avg_rating_today(self, qs):
        rated = qs.filter(rating__isnull=False)
        if not rated.exists():
            return None
        from django.db.models import Avg
        return round(rated.aggregate(avg=Avg("rating"))["avg"], 2)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """REST API for chat messages (primarily read; writes happen over WS)."""

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs.get("session_pk")
        return ChatMessage.objects.filter(session_id=session_id).select_related("sender")
