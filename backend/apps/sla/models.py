"""
SLA models: SLAPolicy, SLARule, Escalation.
"""
import uuid

from django.conf import settings
from django.db import models


class SLAPolicy(models.Model):
    """
    Service Level Agreement policy defining response and resolution targets.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Default policy applied when no specific policy matches",
    )

    # Business hours configuration
    business_hours_only = models.BooleanField(
        default=True,
        help_text="Whether SLA timers count only business hours",
    )
    business_start_hour = models.PositiveSmallIntegerField(default=9)
    business_end_hour = models.PositiveSmallIntegerField(default=17)
    business_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of business days (0=Mon, 6=Sun). Default: Mon-Fri",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "SLA Policy"
        verbose_name_plural = "SLA Policies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.business_days:
            self.business_days = [0, 1, 2, 3, 4]  # Mon-Fri
        # Ensure only one default
        if self.is_default:
            SLAPolicy.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)


class SLARule(models.Model):
    """
    Specific time targets within an SLA policy, scoped by ticket priority.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        SLAPolicy, on_delete=models.CASCADE, related_name="rules",
    )
    priority = models.ForeignKey(
        "tickets.TicketPriority", on_delete=models.CASCADE,
        related_name="sla_rules",
    )

    response_time_minutes = models.PositiveIntegerField(
        help_text="Maximum time (in minutes) to first agent response",
    )
    resolution_time_minutes = models.PositiveIntegerField(
        help_text="Maximum time (in minutes) to resolve the ticket",
    )
    notify_before_breach_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Send a warning notification this many minutes before SLA breach",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["priority__level"]
        unique_together = [("policy", "priority")]

    def __str__(self):
        return f"{self.policy.name} - {self.priority.name}: respond {self.response_time_minutes}m / resolve {self.resolution_time_minutes}m"


class Escalation(models.Model):
    """
    Escalation rules triggered when SLA is breached or approaching breach.
    """

    class TriggerType(models.TextChoices):
        RESPONSE_APPROACHING = "response_approaching", "Response SLA Approaching"
        RESPONSE_BREACHED = "response_breached", "Response SLA Breached"
        RESOLUTION_APPROACHING = "resolution_approaching", "Resolution SLA Approaching"
        RESOLUTION_BREACHED = "resolution_breached", "Resolution SLA Breached"

    class ActionType(models.TextChoices):
        NOTIFY_AGENT = "notify_agent", "Notify Assigned Agent"
        NOTIFY_TEAM_LEAD = "notify_team_lead", "Notify Team Lead"
        NOTIFY_MANAGER = "notify_manager", "Notify Manager"
        REASSIGN = "reassign", "Reassign Ticket"
        INCREASE_PRIORITY = "increase_priority", "Increase Priority"
        CUSTOM_EMAIL = "custom_email", "Send Custom Email"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        SLAPolicy, on_delete=models.CASCADE, related_name="escalations",
    )
    trigger = models.CharField(max_length=30, choices=TriggerType.choices)
    action_type = models.CharField(max_length=30, choices=ActionType.choices)

    notify_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        related_name="sla_escalation_notifications",
        help_text="Users to notify when this escalation fires",
    )
    reassign_to_team = models.ForeignKey(
        "accounts.Team", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="escalation_assignments",
    )
    email_template = models.TextField(
        blank=True, default="",
        help_text="Custom email template body (supports {{ ticket }} placeholders)",
    )

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of escalation execution (lower runs first)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.policy.name}: {self.get_trigger_display()} -> {self.get_action_type_display()}"
