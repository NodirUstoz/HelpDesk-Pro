"""
Serializers for the extended agent models.
"""
from rest_framework import serializers

from .models import AgentSkill, AgentAvailability, AgentPerformance


class AgentSkillSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.user.get_full_name", read_only=True)

    class Meta:
        model = AgentSkill
        fields = [
            "id", "agent", "agent_name", "name", "proficiency",
            "verified", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AgentAvailabilitySerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.user.get_full_name", read_only=True)
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = AgentAvailability
        fields = [
            "id", "agent", "agent_name", "day_of_week", "day_name",
            "start_time", "end_time", "is_active", "timezone_str",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_time")
        end = attrs.get("end_time")
        if start and end and start == end:
            raise serializers.ValidationError(
                "Start time and end time cannot be the same."
            )
        return attrs


class AgentPerformanceSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.user.get_full_name", read_only=True)

    class Meta:
        model = AgentPerformance
        fields = [
            "id", "agent", "agent_name", "date",
            "tickets_assigned", "tickets_resolved", "tickets_reopened",
            "avg_first_response_minutes", "avg_resolution_minutes",
            "sla_compliance_pct",
            "chat_sessions_handled", "avg_chat_duration_minutes",
            "customer_satisfaction_avg", "total_ratings",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AgentPerformanceSummarySerializer(serializers.Serializer):
    """Aggregated performance summary for an agent over a date range."""

    agent_id = serializers.UUIDField()
    agent_name = serializers.CharField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_tickets_assigned = serializers.IntegerField()
    total_tickets_resolved = serializers.IntegerField()
    avg_first_response_minutes = serializers.FloatField()
    avg_resolution_minutes = serializers.FloatField()
    avg_sla_compliance_pct = serializers.FloatField()
    avg_csat = serializers.FloatField()
