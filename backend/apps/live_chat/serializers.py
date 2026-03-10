"""
Serializers for the live chat models.
"""
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True, default="System")
    sender_role = serializers.CharField(source="sender.role", read_only=True, default="system")

    class Meta:
        model = ChatMessage
        fields = [
            "id", "session", "sender", "sender_name", "sender_role",
            "content", "message_type", "file_url", "is_read", "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chat session list views."""

    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    agent_name = serializers.CharField(
        source="agent.get_full_name", read_only=True, default=None
    )
    message_count = serializers.IntegerField(read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    wait_time_seconds = serializers.FloatField(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id", "customer", "customer_name", "customer_email",
            "agent", "agent_name", "subject", "status", "department",
            "message_count", "duration_seconds", "wait_time_seconds",
            "last_message", "started_at", "ended_at",
        ]
        read_only_fields = ["id", "started_at"]

    def get_last_message(self, obj):
        last_msg = obj.messages.exclude(
            message_type=ChatMessage.MessageType.SYSTEM
        ).order_by("-created_at").first()
        if last_msg:
            return {
                "content": last_msg.content[:100],
                "sender_name": last_msg.sender.get_full_name() if last_msg.sender else "System",
                "created_at": last_msg.created_at.isoformat(),
            }
        return None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Full serializer with messages for chat session detail."""

    customer_detail = UserSerializer(source="customer", read_only=True)
    agent_detail = UserSerializer(source="agent", read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    wait_time_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id", "customer", "customer_detail",
            "agent", "agent_detail",
            "subject", "status", "department", "ticket",
            "started_at", "agent_joined_at", "ended_at",
            "duration_seconds", "wait_time_seconds",
            "rating", "rating_comment",
            "customer_ip", "page_url",
            "messages",
        ]
        read_only_fields = ["id", "started_at", "agent_joined_at"]


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for initiating a new chat session."""

    class Meta:
        model = ChatSession
        fields = ["subject", "department"]

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


class ChatSessionRatingSerializer(serializers.Serializer):
    """Serializer for rating a chat session after it ends."""

    rating = serializers.ChoiceField(choices=ChatSession.Rating.choices)
    rating_comment = serializers.CharField(required=False, allow_blank=True, default="")
