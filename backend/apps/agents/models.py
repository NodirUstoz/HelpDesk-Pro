"""
Extended agent models: AgentSkill, AgentAvailability schedule, AgentPerformance metrics.
The core Agent model lives in apps.accounts.models.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Agent


class AgentSkill(models.Model):
    """
    Skills that agents possess, used for intelligent ticket routing.
    """

    class ProficiencyLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(max_length=100)
    proficiency = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.INTERMEDIATE,
    )
    verified = models.BooleanField(
        default=False,
        help_text="Whether this skill has been verified by an admin",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("agent", "name")]

    def __str__(self):
        return f"{self.agent.user.get_full_name()} - {self.name} ({self.proficiency})"


class AgentAvailability(models.Model):
    """
    Scheduled availability windows for agents (work shifts).
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name="availability_schedule"
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    timezone_str = models.CharField(max_length=50, default="UTC")

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name_plural = "Agent Availabilities"
        unique_together = [("agent", "day_of_week", "start_time")]

    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"{self.agent.user.get_full_name()} - {day_name} {self.start_time}-{self.end_time}"

    @property
    def is_currently_active(self):
        """Check if current time falls within this availability window."""
        now = timezone.localtime(timezone.now()).time()
        if self.start_time <= self.end_time:
            return self.start_time <= now <= self.end_time
        # Handle overnight shifts
        return now >= self.start_time or now <= self.end_time


class AgentPerformance(models.Model):
    """
    Daily performance metrics for agents, aggregated from ticket activity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name="performance_records"
    )
    date = models.DateField()

    tickets_assigned = models.PositiveIntegerField(default=0)
    tickets_resolved = models.PositiveIntegerField(default=0)
    tickets_reopened = models.PositiveIntegerField(default=0)

    avg_first_response_minutes = models.FloatField(
        default=0.0,
        help_text="Average first response time in minutes",
    )
    avg_resolution_minutes = models.FloatField(
        default=0.0,
        help_text="Average resolution time in minutes",
    )

    sla_compliance_pct = models.FloatField(
        default=100.0,
        help_text="Percentage of tickets within SLA",
    )

    chat_sessions_handled = models.PositiveIntegerField(default=0)
    avg_chat_duration_minutes = models.FloatField(default=0.0)

    customer_satisfaction_avg = models.FloatField(
        default=0.0,
        help_text="Average CSAT score (1-5)",
    )
    total_ratings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        unique_together = [("agent", "date")]
        verbose_name_plural = "Agent Performance Records"

    def __str__(self):
        return f"{self.agent.user.get_full_name()} - {self.date}"
