"""
Automation engine: evaluates triggers and executes actions.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from .models import AutoRule, Trigger, Action

logger = logging.getLogger(__name__)


class AutomationEngine:
    """
    Core automation engine that evaluates rules against tickets/events.
    """

    @staticmethod
    def process_event(event_type, ticket):
        """
        Find and execute all matching automation rules for the given event.
        """
        rules = AutoRule.objects.filter(
            event_type=event_type,
            is_active=True,
        ).prefetch_related("triggers", "actions").order_by("run_order")

        executed = 0
        for rule in rules:
            if AutomationEngine._evaluate_triggers(rule, ticket):
                AutomationEngine._execute_actions(rule, ticket)
                executed += 1

                # Update execution stats
                rule.execution_count += 1
                rule.last_executed_at = timezone.now()
                rule.save(update_fields=["execution_count", "last_executed_at"])

                logger.info(
                    "Auto rule '%s' fired for ticket %s",
                    rule.name, ticket.ticket_number,
                )

                if rule.stop_processing:
                    break

        return executed

    @staticmethod
    def _evaluate_triggers(rule, ticket):
        """
        Evaluate all triggers for a rule. Returns True if ALL triggers match.
        """
        triggers = rule.triggers.all()
        if not triggers.exists():
            return True  # No triggers means always match

        for trigger in triggers:
            if not AutomationEngine._evaluate_single_trigger(trigger, ticket):
                return False
        return True

    @staticmethod
    def _evaluate_single_trigger(trigger, ticket):
        """Evaluate a single trigger condition against a ticket."""
        field_value = AutomationEngine._get_field_value(trigger.field, ticket)
        operator = trigger.operator
        compare_value = trigger.value

        if operator == Trigger.Operator.IS_SET:
            return field_value is not None and field_value != ""
        if operator == Trigger.Operator.IS_NOT_SET:
            return field_value is None or field_value == ""

        if field_value is None:
            return False

        field_str = str(field_value).lower()
        compare_str = compare_value.lower()

        if operator == Trigger.Operator.EQUALS:
            return field_str == compare_str
        elif operator == Trigger.Operator.NOT_EQUALS:
            return field_str != compare_str
        elif operator == Trigger.Operator.CONTAINS:
            return compare_str in field_str
        elif operator == Trigger.Operator.NOT_CONTAINS:
            return compare_str not in field_str
        elif operator == Trigger.Operator.STARTS_WITH:
            return field_str.startswith(compare_str)
        elif operator == Trigger.Operator.GREATER_THAN:
            try:
                return float(field_value) > float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == Trigger.Operator.LESS_THAN:
            try:
                return float(field_value) < float(compare_value)
            except (ValueError, TypeError):
                return False

        return False

    @staticmethod
    def _get_field_value(field, ticket):
        """Extract the field value from a ticket object."""
        field_map = {
            Trigger.FieldName.SUBJECT: lambda t: t.subject,
            Trigger.FieldName.DESCRIPTION: lambda t: t.description,
            Trigger.FieldName.CHANNEL: lambda t: t.channel,
            Trigger.FieldName.PRIORITY: lambda t: str(t.priority.id) if t.priority else None,
            Trigger.FieldName.STATUS: lambda t: str(t.status.id) if t.status else None,
            Trigger.FieldName.ASSIGNED_AGENT: lambda t: str(t.assigned_agent.id) if t.assigned_agent else None,
            Trigger.FieldName.ASSIGNED_TEAM: lambda t: str(t.assigned_team.id) if t.assigned_team else None,
            Trigger.FieldName.CUSTOMER_EMAIL: lambda t: t.customer.email,
            Trigger.FieldName.CUSTOMER_COMPANY: lambda t: (
                t.customer.customer_profile.company
                if hasattr(t.customer, "customer_profile") else ""
            ),
            Trigger.FieldName.IS_VIP: lambda t: (
                str(t.customer.customer_profile.is_vip)
                if hasattr(t.customer, "customer_profile") else "False"
            ),
            Trigger.FieldName.HOURS_SINCE_CREATED: lambda t: (
                (timezone.now() - t.created_at).total_seconds() / 3600
            ),
            Trigger.FieldName.HOURS_SINCE_UPDATED: lambda t: (
                (timezone.now() - t.updated_at).total_seconds() / 3600
            ),
        }

        extractor = field_map.get(field)
        if extractor:
            try:
                return extractor(ticket)
            except Exception:
                return None
        return None

    @staticmethod
    def _execute_actions(rule, ticket):
        """Execute all actions for a matched rule."""
        for action_obj in rule.actions.all().order_by("order"):
            try:
                AutomationEngine._execute_single_action(action_obj, ticket)
            except Exception as exc:
                logger.error(
                    "Failed to execute action %s (rule: %s, ticket: %s): %s",
                    action_obj.action_type, rule.name, ticket.ticket_number, exc,
                )

    @staticmethod
    def _execute_single_action(action_obj, ticket):
        """Execute a single automation action."""
        action_type = action_obj.action_type
        value = action_obj.value

        if action_type == Action.ActionType.SET_PRIORITY:
            from apps.tickets.models import TicketPriority
            priority = TicketPriority.objects.filter(id=value).first()
            if priority:
                ticket.priority = priority
                ticket.save(update_fields=["priority"])

        elif action_type == Action.ActionType.SET_STATUS:
            from apps.tickets.models import TicketStatus
            status_obj = TicketStatus.objects.filter(id=value).first()
            if status_obj:
                ticket.status = status_obj
                ticket.save(update_fields=["status"])

        elif action_type == Action.ActionType.ASSIGN_AGENT:
            from apps.tickets.services import TicketService
            TicketService.assign_ticket(ticket, agent_id=value)

        elif action_type == Action.ActionType.ASSIGN_TEAM:
            from apps.tickets.services import TicketService
            TicketService.assign_ticket(ticket, team_id=value)

        elif action_type == Action.ActionType.ADD_TAG:
            from apps.tickets.models import TicketTag
            tag = TicketTag.objects.filter(name=value).first()
            if not tag:
                tag = TicketTag.objects.create(name=value)
            ticket.tags.add(tag)

        elif action_type == Action.ActionType.REMOVE_TAG:
            from apps.tickets.models import TicketTag
            tag = TicketTag.objects.filter(name=value).first()
            if tag:
                ticket.tags.remove(tag)

        elif action_type == Action.ActionType.ADD_NOTE:
            from apps.tickets.models import TicketMessage
            TicketMessage.objects.create(
                ticket=ticket,
                sender=None,
                body=value,
                message_type=TicketMessage.MessageType.NOTE,
                is_customer_visible=False,
            )

        elif action_type == Action.ActionType.ESCALATE:
            ticket.is_escalated = True
            ticket.save(update_fields=["is_escalated"])

        elif action_type == Action.ActionType.CLOSE_TICKET:
            from apps.tickets.services import TicketService
            TicketService.close_ticket(ticket)

        elif action_type == Action.ActionType.SEND_NOTIFICATION:
            from apps.notifications.services import NotificationService
            NotificationService.send_ticket_notification(ticket, "automation")

        elif action_type == Action.ActionType.WEBHOOK:
            import requests
            webhook_url = value
            payload = action_obj.extra_data or {}
            payload["ticket_number"] = ticket.ticket_number
            payload["ticket_subject"] = ticket.subject
            try:
                requests.post(webhook_url, json=payload, timeout=10)
            except Exception as exc:
                logger.warning("Webhook to %s failed: %s", webhook_url, exc)

        logger.debug(
            "Executed action '%s' with value '%s' on ticket %s",
            action_type, value, ticket.ticket_number,
        )
