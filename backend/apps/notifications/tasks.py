"""
Celery tasks for sending notifications.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    """
    Send an email for a specific notification.
    """
    from .models import Notification, NotificationPreference

    try:
        notification = Notification.objects.select_related("recipient").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.warning("Notification %s not found", notification_id)
        return

    # Check user preferences
    pref = NotificationPreference.objects.filter(user=notification.recipient).first()
    if pref and pref.digest_enabled:
        logger.info("User %s has digest enabled; skipping individual email", notification.recipient.email)
        return

    # Map notification type to preference field
    pref_map = {
        "ticket_created": "email_ticket_created",
        "ticket_assigned": "email_ticket_assigned",
        "ticket_reply": "email_ticket_reply",
        "ticket_closed": "email_ticket_closed",
        "sla_warning": "email_sla_warning",
        "sla_breach": "email_sla_warning",
        "chat_new": "email_chat_new",
    }

    pref_field = pref_map.get(notification.notification_type)
    if pref and pref_field and not getattr(pref, pref_field, True):
        logger.info(
            "User %s has disabled email for %s",
            notification.recipient.email, notification.notification_type,
        )
        return

    # Send email
    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        notification.is_email_sent = True
        notification.save(update_fields=["is_email_sent"])
        logger.info("Email notification sent to %s", notification.recipient.email)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", notification.recipient.email, exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_daily_digest():
    """
    Send a daily digest of unread notifications to users who have opted in.
    """
    from .models import Notification, NotificationPreference
    from apps.accounts.models import User

    digest_users = NotificationPreference.objects.filter(
        digest_enabled=True
    ).select_related("user")

    for pref in digest_users:
        user = pref.user
        yesterday = timezone.now() - timezone.timedelta(days=1)
        unread = Notification.objects.filter(
            recipient=user,
            is_read=False,
            created_at__gte=yesterday,
        ).order_by("-created_at")

        if not unread.exists():
            continue

        # Build digest content
        lines = [f"Hi {user.first_name},\n\nHere is your daily notification digest:\n"]
        for n in unread[:50]:  # Cap at 50
            lines.append(f"- [{n.get_notification_type_display()}] {n.title}")
        lines.append(f"\nTotal unread: {unread.count()}")
        lines.append("\nLog in to view details: " + getattr(settings, "FRONTEND_URL", "http://localhost:3000"))

        body = "\n".join(lines)

        try:
            send_mail(
                subject=f"HelpDesk Pro - Daily Digest ({unread.count()} notifications)",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Daily digest sent to %s (%d items)", user.email, unread.count())
        except Exception as exc:
            logger.error("Failed to send digest to %s: %s", user.email, exc)


@shared_task
def cleanup_old_notifications(days=90):
    """
    Remove read notifications older than the specified number of days.
    """
    from .models import Notification

    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()

    logger.info("Cleaned up %d old notifications", deleted)
    return {"deleted": deleted}
