"""
Automation models: AutoRule, Trigger, Action.
Provides a rule engine for ticket and chat automations.
"""
import uuid

from django.conf import settings
from django.db import models


class AutoRule(models.Model):
    """
    An automation rule consisting of triggers (conditions) and actions.
    When all triggers match, all actions are executed.
    """

    class EventType(models.TextChoices):
        TICKET_CREATED = "ticket_created", "Ticket Created"
        TICKET_UPDATED = "ticket_updated", "Ticket Updated"
        TICKET_ASSIGNED = "ticket_assigned", "Ticket Assigned"
        TICKET_CLOSED = "ticket_closed", "Ticket Closed"
        CHAT_STARTED = "chat_started", "Chat Started"
        CHAT_ENDED = "chat_ended", "Chat Ended"
        SLA_APPROACHING = "sla_approaching", "SLA Approaching"
        SLA_BREACHED = "sla_breached", "SLA Breached"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    event_type = models.CharField(max_length=30, choices=EventType.choices)

    is_active = models.BooleanField(default=True)
    run_order = models.PositiveIntegerField(
        default=0,
        help_text="Execution order when multiple rules match (lower runs first)",
    )
    stop_processing = models.BooleanField(
        default=False,
        help_text="If True, no further rules are evaluated after this one matches",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_auto_rules",
    )
    execution_count = models.PositiveIntegerField(default=0)
    last_executed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["run_order", "name"]

    def __str__(self):
        return f"{self.name} (on {self.get_event_type_display()})"


class Trigger(models.Model):
    """
    A condition that must be met for the parent AutoRule to fire.
    Multiple triggers on the same rule use AND logic.
    """

    class FieldName(models.TextChoices):
        SUBJECT = "subject", "Subject"
        DESCRIPTION = "description", "Description"
        CHANNEL = "channel", "Channel"
        PRIORITY = "priority", "Priority"
        STATUS = "status", "Status"
        ASSIGNED_AGENT = "assigned_agent", "Assigned Agent"
        ASSIGNED_TEAM = "assigned_team", "Assigned Team"
        CUSTOMER_EMAIL = "customer_email", "Customer Email"
        CUSTOMER_COMPANY = "customer_company", "Customer Company"
        TAG = "tag", "Tag"
        IS_VIP = "is_vip", "Customer is VIP"
        HOURS_SINCE_CREATED = "hours_since_created", "Hours Since Created"
        HOURS_SINCE_UPDATED = "hours_since_updated", "Hours Since Updated"

    class Operator(models.TextChoices):
        EQUALS = "equals", "Equals"
        NOT_EQUALS = "not_equals", "Not Equals"
        CONTAINS = "contains", "Contains"
        NOT_CONTAINS = "not_contains", "Does Not Contain"
        STARTS_WITH = "starts_with", "Starts With"
        GREATER_THAN = "greater_than", "Greater Than"
        LESS_THAN = "less_than", "Less Than"
        IS_SET = "is_set", "Is Set"
        IS_NOT_SET = "is_not_set", "Is Not Set"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AutoRule, on_delete=models.CASCADE, related_name="triggers",
    )
    field = models.CharField(max_length=30, choices=FieldName.choices)
    operator = models.CharField(max_length=20, choices=Operator.choices)
    value = models.CharField(
        max_length=500, blank=True, default="",
        help_text="The value to compare against",
    )

    class Meta:
        ordering = ["field"]

    def __str__(self):
        return f"{self.get_field_display()} {self.get_operator_display()} '{self.value}'"


class Action(models.Model):
    """
    An action to execute when the parent AutoRule's triggers are satisfied.
    """

    class ActionType(models.TextChoices):
        SET_PRIORITY = "set_priority", "Set Priority"
        SET_STATUS = "set_status", "Set Status"
        ASSIGN_AGENT = "assign_agent", "Assign to Agent"
        ASSIGN_TEAM = "assign_team", "Assign to Team"
        ADD_TAG = "add_tag", "Add Tag"
        REMOVE_TAG = "remove_tag", "Remove Tag"
        SEND_EMAIL = "send_email", "Send Email"
        SEND_NOTIFICATION = "send_notification", "Send Notification"
        ADD_NOTE = "add_note", "Add Internal Note"
        ESCALATE = "escalate", "Escalate Ticket"
        CLOSE_TICKET = "close_ticket", "Close Ticket"
        SEND_CANNED_RESPONSE = "send_canned_response", "Send Canned Response"
        WEBHOOK = "webhook", "Fire Webhook"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AutoRule, on_delete=models.CASCADE, related_name="actions",
    )
    action_type = models.CharField(max_length=30, choices=ActionType.choices)
    value = models.CharField(
        max_length=1000, blank=True, default="",
        help_text="Value for the action (e.g., priority ID, agent ID, email template)",
    )
    extra_data = models.JSONField(
        default=dict, blank=True,
        help_text="Additional action configuration",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_action_type_display()}: {self.value[:50]}"
