"""
Ticket models: Ticket, TicketMessage, TicketAttachment, TicketTag, TicketPriority, TicketStatus.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TicketPriority(models.Model):
    """
    Configurable ticket priority levels.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    level = models.PositiveIntegerField(
        unique=True, help_text="Lower number = higher priority"
    )
    color = models.CharField(max_length=7, default="#6B7280")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["level"]
        verbose_name_plural = "Ticket Priorities"

    def __str__(self):
        return self.name


class TicketStatus(models.Model):
    """
    Configurable ticket statuses.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=7, default="#6B7280")
    is_closed = models.BooleanField(
        default=False, help_text="Indicates this status means the ticket is resolved"
    )
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Ticket Statuses"

    def __str__(self):
        return self.name


class TicketTag(models.Model):
    """
    Tags for categorizing tickets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#3B82F6")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """
    Core ticket model representing a support request.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        CHAT = "chat", "Live Chat"
        WEB = "web", "Web Form"
        API = "api", "API"
        PHONE = "phone", "Phone"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    subject = models.CharField(max_length=300)
    description = models.TextField()
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.WEB
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets_as_customer",
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_as_agent",
    )
    assigned_team = models.ForeignKey(
        "accounts.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    priority = models.ForeignKey(
        TicketPriority, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.ForeignKey(
        TicketStatus, on_delete=models.SET_NULL, null=True, blank=True
    )
    tags = models.ManyToManyField(TicketTag, blank=True, related_name="tickets")

    # SLA tracking
    sla_policy = models.ForeignKey(
        "sla.SLAPolicy",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    sla_response_due = models.DateTimeField(null=True, blank=True)
    sla_resolution_due = models.DateTimeField(null=True, blank=True)
    sla_response_breached = models.BooleanField(default=False)
    sla_resolution_breached = models.BooleanField(default=False)

    is_escalated = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticket_number"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["assigned_agent"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self._generate_ticket_number()
        super().save(*args, **kwargs)

    def _generate_ticket_number(self):
        last = Ticket.objects.order_by("-created_at").first()
        if last and last.ticket_number.startswith("HD-"):
            try:
                num = int(last.ticket_number.split("-")[1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"HD-{num:06d}"


class TicketMessage(models.Model):
    """
    Messages / replies within a ticket thread.
    """

    class MessageType(models.TextChoices):
        REPLY = "reply", "Reply"
        NOTE = "note", "Internal Note"
        SYSTEM = "system", "System Message"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    body = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, default=MessageType.REPLY
    )
    is_customer_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on {self.ticket.ticket_number} by {self.sender}"


class TicketAttachment(models.Model):
    """
    File attachments on ticket messages.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        TicketMessage, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="ticket_attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=100, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename
