"""
Notification models for in-app and email notifications.
"""
import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    User notification record for in-app notification center.
    """

    class NotificationType(models.TextChoices):
        TICKET_CREATED = "ticket_created", "Ticket Created"
        TICKET_ASSIGNED = "ticket_assigned", "Ticket Assigned"
        TICKET_UPDATED = "ticket_updated", "Ticket Updated"
        TICKET_CLOSED = "ticket_closed", "Ticket Closed"
        TICKET_REPLY = "ticket_reply", "New Ticket Reply"
        SLA_WARNING = "sla_warning", "SLA Warning"
        SLA_BREACH = "sla_breach", "SLA Breach"
        CHAT_NEW = "chat_new", "New Chat Session"
        CHAT_ASSIGNED = "chat_assigned", "Chat Assigned"
        SYSTEM = "system", "System Notification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Optional references
    ticket_id = models.UUIDField(null=True, blank=True)
    chat_session_id = models.UUIDField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_email_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title} -> {self.recipient}"


class NotificationPreference(models.Model):
    """
    Per-user notification preferences.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    email_ticket_created = models.BooleanField(default=True)
    email_ticket_assigned = models.BooleanField(default=True)
    email_ticket_reply = models.BooleanField(default=True)
    email_ticket_closed = models.BooleanField(default=True)
    email_sla_warning = models.BooleanField(default=True)
    email_chat_new = models.BooleanField(default=True)

    in_app_ticket_created = models.BooleanField(default=True)
    in_app_ticket_assigned = models.BooleanField(default=True)
    in_app_ticket_reply = models.BooleanField(default=True)
    in_app_ticket_closed = models.BooleanField(default=True)
    in_app_sla_warning = models.BooleanField(default=True)
    in_app_chat_new = models.BooleanField(default=True)

    digest_enabled = models.BooleanField(
        default=False,
        help_text="Receive daily digest instead of individual emails",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification prefs for {self.user}"
