"""
Celery configuration for HelpDesk Pro.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("helpdesk")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    "check-sla-breaches-every-5-minutes": {
        "task": "apps.tickets.tasks.check_sla_breaches",
        "schedule": crontab(minute="*/5"),
    },
    "send-pending-survey-emails-every-hour": {
        "task": "apps.satisfaction.tasks.send_pending_surveys",
        "schedule": crontab(minute=0),
    },
    "generate-daily-analytics-report": {
        "task": "apps.analytics.tasks.generate_daily_report",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-stale-chat-sessions-every-30-min": {
        "task": "apps.live_chat.tasks.cleanup_stale_sessions",
        "schedule": crontab(minute="*/30"),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
