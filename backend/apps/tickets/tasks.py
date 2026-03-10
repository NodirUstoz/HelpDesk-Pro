"""
Celery tasks for the tickets app.
"""
import logging

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_sla_breaches(self):
    """
    Periodic task that checks all open tickets for SLA breaches.
    Marks tickets whose response or resolution deadlines have passed.
    """
    from .models import Ticket, TicketStatus

    now = timezone.now()
    open_statuses = TicketStatus.objects.filter(is_closed=False).values_list("id", flat=True)
    open_tickets = Ticket.objects.filter(status__id__in=open_statuses)

    # Check response SLA breaches
    response_breached = open_tickets.filter(
        sla_response_due__lt=now,
        first_response_at__isnull=True,
        sla_response_breached=False,
    )
    response_count = response_breached.update(sla_response_breached=True)

    # Check resolution SLA breaches
    resolution_breached = open_tickets.filter(
        sla_resolution_due__lt=now,
        resolved_at__isnull=True,
        sla_resolution_breached=False,
    )
    resolution_count = resolution_breached.update(sla_resolution_breached=True)

    logger.info(
        "SLA breach check complete: %d response breaches, %d resolution breaches",
        response_count,
        resolution_count,
    )

    # Trigger escalation for newly breached tickets
    if response_count > 0 or resolution_count > 0:
        escalate_breached_tickets.delay()

    return {
        "response_breaches": response_count,
        "resolution_breaches": resolution_count,
    }


@shared_task(bind=True, max_retries=3)
def escalate_breached_tickets(self):
    """
    Auto-escalate tickets that have SLA breaches but are not yet escalated.
    """
    from .models import Ticket, TicketMessage

    tickets = Ticket.objects.filter(
        Q(sla_response_breached=True) | Q(sla_resolution_breached=True),
        is_escalated=False,
    )

    escalated_count = 0
    for ticket in tickets:
        ticket.is_escalated = True
        ticket.save(update_fields=["is_escalated"])

        TicketMessage.objects.create(
            ticket=ticket,
            sender=None,
            body="Ticket auto-escalated due to SLA breach.",
            message_type=TicketMessage.MessageType.SYSTEM,
            is_customer_visible=False,
        )
        escalated_count += 1

    logger.info("Auto-escalated %d tickets due to SLA breaches", escalated_count)
    return {"escalated": escalated_count}


@shared_task(bind=True, max_retries=3)
def send_ticket_notification(self, ticket_id, event_type):
    """
    Send notification when a ticket event occurs (created, assigned, updated, etc.).
    """
    from .models import Ticket
    from apps.notifications.services import NotificationService

    try:
        ticket = Ticket.objects.select_related(
            "customer", "assigned_agent", "priority", "status"
        ).get(id=ticket_id)
    except Ticket.DoesNotExist:
        logger.warning("Ticket %s not found for notification", ticket_id)
        return

    NotificationService.send_ticket_notification(ticket, event_type)


@shared_task
def auto_close_stale_tickets(days_inactive=7):
    """
    Automatically close tickets that have had no activity for the specified
    number of days and are currently in a 'waiting for customer' state.
    """
    from .models import Ticket, TicketMessage, TicketStatus

    cutoff = timezone.now() - timezone.timedelta(days=days_inactive)
    waiting_status = TicketStatus.objects.filter(
        slug="waiting-for-customer"
    ).first()

    if not waiting_status:
        logger.info("No 'waiting-for-customer' status found; skipping auto-close.")
        return {"auto_closed": 0}

    stale_tickets = Ticket.objects.filter(
        status=waiting_status,
        updated_at__lt=cutoff,
    )

    closed_status = TicketStatus.objects.filter(is_closed=True).first()
    closed_count = 0

    for ticket in stale_tickets:
        if closed_status:
            ticket.status = closed_status
        ticket.resolved_at = timezone.now()
        ticket.save(update_fields=["status", "resolved_at"])

        TicketMessage.objects.create(
            ticket=ticket,
            sender=None,
            body=f"Ticket auto-closed after {days_inactive} days of inactivity.",
            message_type=TicketMessage.MessageType.SYSTEM,
        )
        closed_count += 1

    logger.info("Auto-closed %d stale tickets", closed_count)
    return {"auto_closed": closed_count}
