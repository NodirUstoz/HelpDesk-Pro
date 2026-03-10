"""
Live chat models: ChatSession, ChatMessage.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    """
    Represents a live chat session between a customer and an agent.
    """

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On Hold"
        CLOSED = "closed", "Closed"

    class Rating(models.IntegerChoices):
        TERRIBLE = 1, "Terrible"
        BAD = 2, "Bad"
        OKAY = 3, "Okay"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="chat_sessions_as_customer",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="chat_sessions_as_agent",
    )
    subject = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITING,
    )
    department = models.CharField(max_length=100, blank=True, default="")

    # Link to ticket if chat was converted
    ticket = models.ForeignKey(
        "tickets.Ticket", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="chat_sessions",
    )

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    agent_joined_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Satisfaction
    rating = models.PositiveSmallIntegerField(
        choices=Rating.choices, null=True, blank=True,
    )
    rating_comment = models.TextField(blank=True, default="")

    # Metadata
    customer_ip = models.GenericIPAddressField(null=True, blank=True)
    customer_user_agent = models.TextField(blank=True, default="")
    page_url = models.URLField(blank=True, default="", help_text="Page the customer initiated chat from")

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["agent"]),
            models.Index(fields=["-started_at"]),
        ]

    def __str__(self):
        return f"Chat {self.id} - {self.customer} ({self.status})"

    @property
    def duration_seconds(self):
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds()
        if self.started_at:
            return (timezone.now() - self.started_at).total_seconds()
        return 0

    @property
    def wait_time_seconds(self):
        if self.agent_joined_at and self.started_at:
            return (self.agent_joined_at - self.started_at).total_seconds()
        return 0

    @property
    def message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """
    Individual messages within a chat session.
    """

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        FILE = "file", "File"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, default=MessageType.TEXT,
    )
    file_url = models.URLField(blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self):
        sender_name = self.sender.get_full_name() if self.sender else "System"
        return f"{sender_name}: {self.content[:50]}"
