"""
Serializers for automation models.
"""
from rest_framework import serializers

from .models import AutoRule, Trigger, Action


class TriggerSerializer(serializers.ModelSerializer):
    field_display = serializers.CharField(source="get_field_display", read_only=True)
    operator_display = serializers.CharField(source="get_operator_display", read_only=True)

    class Meta:
        model = Trigger
        fields = [
            "id", "rule", "field", "field_display",
            "operator", "operator_display", "value",
        ]
        read_only_fields = ["id"]


class ActionSerializer(serializers.ModelSerializer):
    action_type_display = serializers.CharField(source="get_action_type_display", read_only=True)

    class Meta:
        model = Action
        fields = [
            "id", "rule", "action_type", "action_type_display",
            "value", "extra_data", "order",
        ]
        read_only_fields = ["id"]


class AutoRuleListSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    trigger_count = serializers.SerializerMethodField()
    action_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = AutoRule
        fields = [
            "id", "name", "description", "event_type", "event_type_display",
            "is_active", "run_order", "stop_processing",
            "created_by", "created_by_name",
            "execution_count", "last_executed_at",
            "trigger_count", "action_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "execution_count", "last_executed_at", "created_at", "updated_at"]

    def get_trigger_count(self, obj):
        return obj.triggers.count()

    def get_action_count(self, obj):
        return obj.actions.count()


class AutoRuleDetailSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    triggers = TriggerSerializer(many=True, read_only=True)
    actions = ActionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = AutoRule
        fields = [
            "id", "name", "description", "event_type", "event_type_display",
            "is_active", "run_order", "stop_processing",
            "created_by", "created_by_name",
            "execution_count", "last_executed_at",
            "triggers", "actions",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "execution_count", "last_executed_at",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
