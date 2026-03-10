"""
Views for agent skills, availability, and performance.
"""
from datetime import timedelta

from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Agent
from apps.accounts.permissions import IsAdminOrAgent, IsAdmin
from .models import AgentSkill, AgentAvailability, AgentPerformance
from .serializers import (
    AgentSkillSerializer,
    AgentAvailabilitySerializer,
    AgentPerformanceSerializer,
    AgentPerformanceSummarySerializer,
)


class AgentSkillViewSet(viewsets.ModelViewSet):
    """CRUD for agent skills."""

    serializer_class = AgentSkillSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["agent", "proficiency", "verified"]
    search_fields = ["name"]

    def get_queryset(self):
        qs = AgentSkill.objects.select_related("agent__user").all()
        agent_id = self.request.query_params.get("agent_id")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def verify(self, request, pk=None):
        """Admin verifies an agent skill."""
        skill = self.get_object()
        skill.verified = True
        skill.save(update_fields=["verified"])
        return Response(AgentSkillSerializer(skill).data)


class AgentAvailabilityViewSet(viewsets.ModelViewSet):
    """CRUD for agent availability schedules."""

    serializer_class = AgentAvailabilitySerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["agent", "day_of_week", "is_active"]

    def get_queryset(self):
        qs = AgentAvailability.objects.select_related("agent__user").all()
        agent_id = self.request.query_params.get("agent_id")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs

    @action(detail=False, methods=["get"])
    def currently_available(self, request):
        """Return agents whose schedule covers the current time."""
        now = timezone.localtime(timezone.now())
        current_day = now.weekday()
        current_time = now.time()

        available_schedules = AgentAvailability.objects.filter(
            is_active=True,
            day_of_week=current_day,
            start_time__lte=current_time,
            end_time__gte=current_time,
        ).select_related("agent__user")

        serializer = AgentAvailabilitySerializer(available_schedules, many=True)
        return Response(serializer.data)


class AgentPerformanceViewSet(viewsets.ModelViewSet):
    """Agent performance metrics. Read-only for agents; full access for admins."""

    serializer_class = AgentPerformanceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrAgent]
    filterset_fields = ["agent", "date"]
    ordering_fields = ["date", "tickets_resolved", "sla_compliance_pct"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = AgentPerformance.objects.select_related("agent__user").all()
        # Agents can only see their own performance
        if self.request.user.is_agent and not self.request.user.is_admin:
            qs = qs.filter(agent__user=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Aggregated performance summary for a given agent and date range.
        Query params: agent_id, days (default 30).
        """
        agent_id = request.query_params.get("agent_id")
        days = int(request.query_params.get("days", 30))

        if not agent_id:
            return Response(
                {"error": "agent_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            agent = Agent.objects.select_related("user").get(id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {"error": "Agent not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        period_end = timezone.now().date()
        period_start = period_end - timedelta(days=days)

        records = AgentPerformance.objects.filter(
            agent=agent,
            date__gte=period_start,
            date__lte=period_end,
        )

        aggregated = records.aggregate(
            total_assigned=Sum("tickets_assigned"),
            total_resolved=Sum("tickets_resolved"),
            avg_frt=Avg("avg_first_response_minutes"),
            avg_rt=Avg("avg_resolution_minutes"),
            avg_sla=Avg("sla_compliance_pct"),
            avg_csat=Avg("customer_satisfaction_avg"),
        )

        summary_data = {
            "agent_id": agent.id,
            "agent_name": agent.user.get_full_name(),
            "period_start": period_start,
            "period_end": period_end,
            "total_tickets_assigned": aggregated["total_assigned"] or 0,
            "total_tickets_resolved": aggregated["total_resolved"] or 0,
            "avg_first_response_minutes": round(aggregated["avg_frt"] or 0, 2),
            "avg_resolution_minutes": round(aggregated["avg_rt"] or 0, 2),
            "avg_sla_compliance_pct": round(aggregated["avg_sla"] or 0, 2),
            "avg_csat": round(aggregated["avg_csat"] or 0, 2),
        }

        serializer = AgentPerformanceSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def leaderboard(self, request):
        """
        Return top-performing agents ranked by tickets resolved in the last N days.
        """
        days = int(request.query_params.get("days", 30))
        limit = int(request.query_params.get("limit", 10))
        period_start = timezone.now().date() - timedelta(days=days)

        top_agents = (
            AgentPerformance.objects.filter(date__gte=period_start)
            .values("agent__id", "agent__user__first_name", "agent__user__last_name")
            .annotate(
                total_resolved=Sum("tickets_resolved"),
                avg_csat=Avg("customer_satisfaction_avg"),
                avg_sla=Avg("sla_compliance_pct"),
            )
            .order_by("-total_resolved")[:limit]
        )

        results = [
            {
                "agent_id": entry["agent__id"],
                "agent_name": f"{entry['agent__user__first_name']} {entry['agent__user__last_name']}",
                "total_resolved": entry["total_resolved"],
                "avg_csat": round(entry["avg_csat"] or 0, 2),
                "avg_sla_compliance": round(entry["avg_sla"] or 0, 2),
            }
            for entry in top_agents
        ]

        return Response(results)
