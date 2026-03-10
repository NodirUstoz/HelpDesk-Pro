"""
Views for SLA policy management.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin, IsAdminOrAgent
from .models import SLAPolicy, SLARule, Escalation
from .serializers import (
    SLAPolicyListSerializer,
    SLAPolicyDetailSerializer,
    SLARuleSerializer,
    EscalationSerializer,
)


class SLAPolicyViewSet(viewsets.ModelViewSet):
    """CRUD for SLA policies. Admin-only for writes, agents can read."""

    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["is_active", "is_default"]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return SLAPolicyListSerializer
        return SLAPolicyDetailSerializer

    def get_queryset(self):
        return SLAPolicy.objects.prefetch_related("rules", "escalations").all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdmin()]
        return super().get_permissions()


class SLARuleViewSet(viewsets.ModelViewSet):
    """CRUD for SLA rules within a policy."""

    serializer_class = SLARuleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["policy", "priority"]

    def get_queryset(self):
        qs = SLARule.objects.select_related("policy", "priority").all()
        policy_id = self.request.query_params.get("policy_id")
        if policy_id:
            qs = qs.filter(policy_id=policy_id)
        return qs


class EscalationViewSet(viewsets.ModelViewSet):
    """CRUD for escalation rules."""

    serializer_class = EscalationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["policy", "trigger", "action_type", "is_active"]

    def get_queryset(self):
        qs = Escalation.objects.select_related("policy").all()
        policy_id = self.request.query_params.get("policy_id")
        if policy_id:
            qs = qs.filter(policy_id=policy_id)
        return qs
