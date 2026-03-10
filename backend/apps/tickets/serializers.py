"""
Serializers for ticket models.
"""
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Ticket, TicketMessage, TicketAttachment, TicketTag, TicketPriority, TicketStatus


class TicketPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketPriority
        fields = ["id", "name", "level", "color", "description", "is_active"]


class TicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatus
        fields = ["id", "name", "slug", "color", "is_closed", "order", "is_default"]


class TicketTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTag
        fields = ["id", "name", "color"]


class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "filename", "file_size", "content_type", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_detail = UserSerializer(source="sender", read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketMessage
        fields = [
            "id", "ticket", "sender", "sender_detail", "body",
            "message_type", "is_customer_visible", "attachments", "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for ticket list views."""

    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    agent_name = serializers.CharField(
        source="assigned_agent.get_full_name", read_only=True, default=None
    )
    priority_detail = TicketPrioritySerializer(source="priority", read_only=True)
    status_detail = TicketStatusSerializer(source="status", read_only=True)
    tags_detail = TicketTagSerializer(source="tags", many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id", "ticket_number", "subject", "channel",
            "customer", "customer_name", "customer_email",
            "assigned_agent", "agent_name", "assigned_team",
            "priority", "priority_detail", "status", "status_detail",
            "tags", "tags_detail", "message_count",
            "is_escalated", "is_spam",
            "sla_response_breached", "sla_resolution_breached",
            "first_response_at", "resolved_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "ticket_number", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class TicketDetailSerializer(serializers.ModelSerializer):
    """Full serializer for ticket detail views with nested messages."""

    customer_detail = UserSerializer(source="customer", read_only=True)
    agent_detail = UserSerializer(source="assigned_agent", read_only=True)
    priority_detail = TicketPrioritySerializer(source="priority", read_only=True)
    status_detail = TicketStatusSerializer(source="status", read_only=True)
    tags_detail = TicketTagSerializer(source="tags", many=True, read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id", "ticket_number", "subject", "description", "channel",
            "customer", "customer_detail",
            "assigned_agent", "agent_detail", "assigned_team",
            "priority", "priority_detail", "status", "status_detail",
            "tags", "tags_detail",
            "sla_policy", "first_response_at", "resolved_at",
            "sla_response_due", "sla_resolution_due",
            "sla_response_breached", "sla_resolution_breached",
            "is_escalated", "is_spam",
            "messages", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "ticket_number", "first_response_at", "resolved_at",
            "created_at", "updated_at",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tickets."""

    class Meta:
        model = Ticket
        fields = [
            "subject", "description", "channel", "priority",
            "tags", "assigned_team",
        ]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        user = self.context["request"].user
        validated_data["customer"] = user

        # Set default status
        default_status = TicketStatus.objects.filter(is_default=True).first()
        if default_status:
            validated_data["status"] = default_status

        ticket = Ticket.objects.create(**validated_data)
        if tags:
            ticket.tags.set(tags)

        return ticket


class TicketAssignSerializer(serializers.Serializer):
    """Serializer for ticket assignment."""

    assigned_agent = serializers.UUIDField(required=False, allow_null=True)
    assigned_team = serializers.UUIDField(required=False, allow_null=True)
