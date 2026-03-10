"""
Report models for storing generated report snapshots.
"""
import uuid

from django.conf import settings
from django.db import models


class Report(models.Model):
    """
    Stored report snapshot with cached data.
    """

    class ReportType(models.TextChoices):
        TICKET_SUMMARY = "ticket_summary", "Ticket Summary"
        AGENT_PERFORMANCE = "agent_performance", "Agent Performance"
        SLA_COMPLIANCE = "sla_compliance", "SLA Compliance"
        CUSTOMER_SATISFACTION = "customer_satisfaction", "Customer Satisfaction"
        CHANNEL_BREAKDOWN = "channel_breakdown", "Channel Breakdown"
        VOLUME_TRENDS = "volume_trends", "Volume Trends"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="generated_reports",
    )

    date_from = models.DateField()
    date_to = models.DateField()
    filters = models.JSONField(
        default=dict, blank=True,
        help_text="Additional filters applied when generating this report",
    )
    data = models.JSONField(
        default=dict, blank=True,
        help_text="Cached report data",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.date_from} to {self.date_to})"


class ScheduledReport(models.Model):
    """
    Configuration for automatically generated recurring reports.
    """

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=Report.ReportType.choices)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="subscribed_reports",
    )
    filters = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.frequency})"
