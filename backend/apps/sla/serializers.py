"""
Serializers for SLA models.
"""
from rest_framework import serializers

from .models import SLAPolicy, SLARule, Escalation


class SLARuleSerializer(serializers.ModelSerializer):
    priority_name = serializers.CharField(source="priority.name", read_only=True)

    class Meta:
        model = SLARule
        fields = [
            "id", "policy", "priority", "priority_name",
            "response_time_minutes", "resolution_time_minutes",
            "notify_before_breach_minutes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EscalationSerializer(serializers.ModelSerializer):
    trigger_display = serializers.CharField(source="get_trigger_display", read_only=True)
    action_display = serializers.CharField(source="get_action_type_display", read_only=True)

    class Meta:
        model = Escalation
        fields = [
            "id", "policy", "trigger", "trigger_display",
            "action_type", "action_display",
            "notify_users", "reassign_to_team", "email_template",
            "is_active", "order", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SLAPolicyListSerializer(serializers.ModelSerializer):
    rule_count = serializers.SerializerMethodField()
    escalation_count = serializers.SerializerMethodField()

    class Meta:
        model = SLAPolicy
        fields = [
            "id", "name", "description", "is_active", "is_default",
            "business_hours_only", "rule_count", "escalation_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_rule_count(self, obj):
        return obj.rules.count()

    def get_escalation_count(self, obj):
        return obj.escalations.count()


class SLAPolicyDetailSerializer(serializers.ModelSerializer):
    rules = SLARuleSerializer(many=True, read_only=True)
    escalations = EscalationSerializer(many=True, read_only=True)

    class Meta:
        model = SLAPolicy
        fields = [
            "id", "name", "description", "is_active", "is_default",
            "business_hours_only", "business_start_hour", "business_end_hour",
            "business_days", "rules", "escalations",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
