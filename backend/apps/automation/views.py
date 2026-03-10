"""
Views for automation rule management.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin
from .models import AutoRule, Trigger, Action
from .serializers import (
    AutoRuleListSerializer,
    AutoRuleDetailSerializer,
    TriggerSerializer,
    ActionSerializer,
)


class AutoRuleViewSet(viewsets.ModelViewSet):
    """CRUD for automation rules. Admin-only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["event_type", "is_active"]
    search_fields = ["name", "description"]
    ordering = ["run_order", "name"]

    def get_serializer_class(self):
        if self.action == "list":
            return AutoRuleListSerializer
        return AutoRuleDetailSerializer

    def get_queryset(self):
        return AutoRule.objects.prefetch_related("triggers", "actions").all()

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """Toggle a rule's active state."""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save(update_fields=["is_active"])
        return Response(AutoRuleListSerializer(rule).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Duplicate an existing rule with its triggers and actions."""
        original = self.get_object()
        new_rule = AutoRule.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            event_type=original.event_type,
            is_active=False,
            run_order=original.run_order,
            stop_processing=original.stop_processing,
            created_by=request.user,
        )

        for trigger in original.triggers.all():
            Trigger.objects.create(
                rule=new_rule,
                field=trigger.field,
                operator=trigger.operator,
                value=trigger.value,
            )

        for action_obj in original.actions.all():
            Action.objects.create(
                rule=new_rule,
                action_type=action_obj.action_type,
                value=action_obj.value,
                extra_data=action_obj.extra_data,
                order=action_obj.order,
            )

        return Response(AutoRuleDetailSerializer(new_rule).data)


class TriggerViewSet(viewsets.ModelViewSet):
    """CRUD for triggers on automation rules."""

    serializer_class = TriggerSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["rule", "field", "operator"]

    def get_queryset(self):
        qs = Trigger.objects.all()
        rule_id = self.request.query_params.get("rule_id")
        if rule_id:
            qs = qs.filter(rule_id=rule_id)
        return qs


class ActionViewSet(viewsets.ModelViewSet):
    """CRUD for actions on automation rules."""

    serializer_class = ActionSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["rule", "action_type"]

    def get_queryset(self):
        qs = Action.objects.all()
        rule_id = self.request.query_params.get("rule_id")
        if rule_id:
            qs = qs.filter(rule_id=rule_id)
        return qs
