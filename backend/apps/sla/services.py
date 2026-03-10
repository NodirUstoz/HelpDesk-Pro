"""
SLA business logic services.
"""
import logging
from datetime import timedelta, datetime, time

from django.utils import timezone

from .models import SLAPolicy, SLARule, Escalation

logger = logging.getLogger(__name__)


class SLAService:
    """Service class for SLA-related business logic."""

    @staticmethod
    def calculate_due_date(start_time, duration_minutes, policy):
        """
        Calculate the SLA due date, optionally considering business hours.
        If business_hours_only is False, simply adds duration_minutes.
        Otherwise, only counts minutes within business hours.
        """
        if not policy.business_hours_only:
            return start_time + timedelta(minutes=duration_minutes)

        remaining_minutes = duration_minutes
        current = start_time
        business_days = policy.business_days or [0, 1, 2, 3, 4]
        biz_start = time(policy.business_start_hour, 0)
        biz_end = time(policy.business_end_hour, 0)
        biz_day_minutes = (policy.business_end_hour - policy.business_start_hour) * 60

        max_iterations = duration_minutes + 1440  # safety limit
        iteration = 0

        while remaining_minutes > 0 and iteration < max_iterations:
            iteration += 1
            current_date = current.date()
            current_time = current.time()
            weekday = current_date.weekday()

            # Skip non-business days
            if weekday not in business_days:
                current = timezone.make_aware(
                    datetime.combine(current_date + timedelta(days=1), biz_start),
                    timezone.get_current_timezone(),
                )
                continue

            # Before business hours - jump to start
            if current_time < biz_start:
                current = current.replace(
                    hour=policy.business_start_hour, minute=0, second=0, microsecond=0
                )
                current_time = biz_start

            # After business hours - jump to next business day
            if current_time >= biz_end:
                next_day = current_date + timedelta(days=1)
                current = timezone.make_aware(
                    datetime.combine(next_day, biz_start),
                    timezone.get_current_timezone(),
                )
                continue

            # Calculate available minutes today
            end_of_biz = current.replace(
                hour=policy.business_end_hour, minute=0, second=0, microsecond=0
            )
            available = (end_of_biz - current).total_seconds() / 60

            if remaining_minutes <= available:
                current += timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                remaining_minutes -= available
                next_day = current_date + timedelta(days=1)
                current = timezone.make_aware(
                    datetime.combine(next_day, biz_start),
                    timezone.get_current_timezone(),
                )

        return current

    @staticmethod
    def get_applicable_policy(ticket):
        """
        Determine which SLA policy applies to a ticket.
        Checks priority-specific policies first, then falls back to default.
        """
        if ticket.priority:
            policy = SLAPolicy.objects.filter(
                is_active=True,
                rules__priority=ticket.priority,
            ).first()
            if policy:
                return policy

        return SLAPolicy.objects.filter(is_active=True, is_default=True).first()

    @staticmethod
    def apply_policy_to_ticket(ticket):
        """
        Apply the appropriate SLA policy to a ticket, setting due dates.
        """
        policy = SLAService.get_applicable_policy(ticket)
        if not policy:
            logger.info("No SLA policy found for ticket %s", ticket.ticket_number)
            return ticket

        ticket.sla_policy = policy
        rule = policy.rules.filter(priority=ticket.priority).first()

        now = timezone.now()
        if rule:
            ticket.sla_response_due = SLAService.calculate_due_date(
                now, rule.response_time_minutes, policy
            )
            ticket.sla_resolution_due = SLAService.calculate_due_date(
                now, rule.resolution_time_minutes, policy
            )
        else:
            from django.conf import settings
            ticket.sla_response_due = now + timedelta(
                minutes=getattr(settings, "DEFAULT_SLA_RESPONSE_TIME", 60)
            )
            ticket.sla_resolution_due = now + timedelta(
                minutes=getattr(settings, "DEFAULT_SLA_RESOLUTION_TIME", 480)
            )

        ticket.save(update_fields=[
            "sla_policy", "sla_response_due", "sla_resolution_due",
        ])

        logger.info(
            "SLA policy '%s' applied to ticket %s (response due: %s, resolution due: %s)",
            policy.name, ticket.ticket_number,
            ticket.sla_response_due, ticket.sla_resolution_due,
        )
        return ticket

    @staticmethod
    def execute_escalations(ticket, trigger_type):
        """
        Execute all active escalation rules for a given trigger type.
        """
        if not ticket.sla_policy:
            return

        escalations = Escalation.objects.filter(
            policy=ticket.sla_policy,
            trigger=trigger_type,
            is_active=True,
        ).order_by("order")

        for escalation in escalations:
            try:
                SLAService._execute_escalation_action(ticket, escalation)
            except Exception as exc:
                logger.error(
                    "Failed to execute escalation %s for ticket %s: %s",
                    escalation.id, ticket.ticket_number, exc,
                )

    @staticmethod
    def _execute_escalation_action(ticket, escalation):
        """Execute a single escalation action."""
        from apps.tickets.models import TicketMessage

        if escalation.action_type == Escalation.ActionType.INCREASE_PRIORITY:
            from apps.tickets.models import TicketPriority
            higher = TicketPriority.objects.filter(
                level__lt=ticket.priority.level if ticket.priority else 999,
                is_active=True,
            ).order_by("-level").first()
            if higher:
                ticket.priority = higher
                ticket.save(update_fields=["priority"])
                TicketMessage.objects.create(
                    ticket=ticket, sender=None,
                    body=f"Priority escalated to {higher.name} due to SLA {escalation.get_trigger_display()}.",
                    message_type=TicketMessage.MessageType.SYSTEM,
                    is_customer_visible=False,
                )

        elif escalation.action_type == Escalation.ActionType.REASSIGN:
            if escalation.reassign_to_team:
                from apps.tickets.services import TicketService
                TicketService.assign_ticket(ticket, team_id=escalation.reassign_to_team.id)

        elif escalation.action_type in (
            Escalation.ActionType.NOTIFY_AGENT,
            Escalation.ActionType.NOTIFY_TEAM_LEAD,
            Escalation.ActionType.NOTIFY_MANAGER,
        ):
            from apps.notifications.services import NotificationService
            users = list(escalation.notify_users.all())
            if escalation.action_type == Escalation.ActionType.NOTIFY_AGENT and ticket.assigned_agent:
                users.append(ticket.assigned_agent)
            for user in users:
                NotificationService.send_sla_warning(ticket, user, escalation.get_trigger_display())

        logger.info(
            "Escalation action '%s' executed for ticket %s",
            escalation.get_action_type_display(), ticket.ticket_number,
        )
