"""
Notification service: creates notifications and triggers email delivery.
"""
import logging

from django.utils import timezone

from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized service for creating and dispatching notifications.
    """

    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        ticket_id=None,
        chat_session_id=None,
        send_email=True,
    ):
        """
        Create an in-app notification and optionally queue an email.
        """
        # Check in-app preference
        pref = NotificationPreference.objects.filter(user=recipient).first()
        pref_map = {
            Notification.NotificationType.TICKET_CREATED: "in_app_ticket_created",
            Notification.NotificationType.TICKET_ASSIGNED: "in_app_ticket_assigned",
            Notification.NotificationType.TICKET_REPLY: "in_app_ticket_reply",
            Notification.NotificationType.TICKET_CLOSED: "in_app_ticket_closed",
            Notification.NotificationType.SLA_WARNING: "in_app_sla_warning",
            Notification.NotificationType.SLA_BREACH: "in_app_sla_warning",
            Notification.NotificationType.CHAT_NEW: "in_app_chat_new",
        }

        pref_field = pref_map.get(notification_type)
        if pref and pref_field and not getattr(pref, pref_field, True):
            logger.debug(
                "In-app notification disabled for %s (%s)",
                recipient.email, notification_type,
            )
            return None

        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            ticket_id=ticket_id,
            chat_session_id=chat_session_id,
        )

        # Queue email asynchronously
        if send_email:
            from .tasks import send_email_notification
            send_email_notification.delay(str(notification.id))

        return notification

    @staticmethod
    def send_ticket_notification(ticket, event_type):
        """
        Send appropriate notifications when a ticket event occurs.
        """
        type_map = {
            "created": Notification.NotificationType.TICKET_CREATED,
            "assigned": Notification.NotificationType.TICKET_ASSIGNED,
            "updated": Notification.NotificationType.TICKET_UPDATED,
            "closed": Notification.NotificationType.TICKET_CLOSED,
            "reply": Notification.NotificationType.TICKET_REPLY,
            "automation": Notification.NotificationType.SYSTEM,
        }
        notification_type = type_map.get(event_type, Notification.NotificationType.SYSTEM)

        title_map = {
            "created": f"New ticket: {ticket.ticket_number}",
            "assigned": f"Ticket {ticket.ticket_number} assigned to you",
            "updated": f"Ticket {ticket.ticket_number} updated",
            "closed": f"Ticket {ticket.ticket_number} closed",
            "reply": f"New reply on {ticket.ticket_number}",
            "automation": f"Automation triggered on {ticket.ticket_number}",
        }
        title = title_map.get(event_type, f"Ticket {ticket.ticket_number} notification")

        message = f"Ticket: {ticket.ticket_number}\nSubject: {ticket.subject}"

        recipients = set()

        if event_type == "created" and ticket.assigned_agent:
            recipients.add(ticket.assigned_agent)
        elif event_type == "assigned" and ticket.assigned_agent:
            recipients.add(ticket.assigned_agent)
        elif event_type in ("reply", "updated"):
            # Notify customer and agent
            if ticket.customer:
                recipients.add(ticket.customer)
            if ticket.assigned_agent:
                recipients.add(ticket.assigned_agent)
        elif event_type == "closed":
            if ticket.customer:
                recipients.add(ticket.customer)

        for recipient in recipients:
            NotificationService.create_notification(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                ticket_id=ticket.id,
            )

    @staticmethod
    def send_sla_warning(ticket, user, trigger_description):
        """Send an SLA warning notification to a specific user."""
        NotificationService.create_notification(
            recipient=user,
            notification_type=Notification.NotificationType.SLA_WARNING,
            title=f"SLA Warning: {ticket.ticket_number}",
            message=(
                f"Ticket {ticket.ticket_number} has triggered: {trigger_description}.\n"
                f"Subject: {ticket.subject}\n"
                f"Response due: {ticket.sla_response_due}\n"
                f"Resolution due: {ticket.sla_resolution_due}"
            ),
            ticket_id=ticket.id,
        )

    @staticmethod
    def send_chat_notification(session, event_type):
        """Send notification for chat events."""
        if event_type == "new" and session.agent:
            NotificationService.create_notification(
                recipient=session.agent,
                notification_type=Notification.NotificationType.CHAT_NEW,
                title=f"New chat session waiting",
                message=f"Customer {session.customer.get_full_name()} is waiting for support.",
                chat_session_id=session.id,
            )

    @staticmethod
    def mark_as_read(notification_ids, user):
        """Mark specific notifications as read."""
        updated = Notification.objects.filter(
            id__in=notification_ids,
            recipient=user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return updated

    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user."""
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def get_unread_count(user):
        """Get the unread notification count for a user."""
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).count()
