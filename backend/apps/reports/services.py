"""
Report generation services.
"""
import logging
from datetime import timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating various report types."""

    @staticmethod
    def ticket_summary(date_from, date_to, filters=None):
        """
        Generate a ticket summary report for the given date range.
        Returns counts by status, priority, channel, and daily volume.
        """
        from apps.tickets.models import Ticket, TicketStatus

        base_qs = Ticket.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        if filters and filters.get("team_id"):
            base_qs = base_qs.filter(assigned_team_id=filters["team_id"])

        total = base_qs.count()
        closed_statuses = TicketStatus.objects.filter(is_closed=True).values_list("id", flat=True)
        resolved = base_qs.filter(status_id__in=closed_statuses).count()

        by_status = list(
            base_qs.values("status__name", "status__color")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_priority = list(
            base_qs.values("priority__name", "priority__color", "priority__level")
            .annotate(count=Count("id"))
            .order_by("priority__level")
        )

        by_channel = list(
            base_qs.values("channel")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        daily_volume = list(
            base_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                created=Count("id"),
                resolved_count=Count("id", filter=Q(status_id__in=closed_statuses)),
            )
            .order_by("date")
        )

        # Serialize dates for JSON
        for entry in daily_volume:
            entry["date"] = entry["date"].isoformat()

        return {
            "total_tickets": total,
            "resolved_tickets": resolved,
            "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_channel": by_channel,
            "daily_volume": daily_volume,
        }

    @staticmethod
    def agent_performance_report(date_from, date_to, filters=None):
        """
        Generate an agent performance report.
        """
        from apps.agents.models import AgentPerformance
        from apps.accounts.models import Agent

        agents_qs = Agent.objects.select_related("user").all()
        if filters and filters.get("team_id"):
            agents_qs = agents_qs.filter(team_id=filters["team_id"])

        results = []
        for agent in agents_qs:
            records = AgentPerformance.objects.filter(
                agent=agent,
                date__gte=date_from,
                date__lte=date_to,
            )

            agg = records.aggregate(
                total_assigned=Count("tickets_assigned"),
                total_resolved=Count("tickets_resolved"),
                avg_frt=Avg("avg_first_response_minutes"),
                avg_rt=Avg("avg_resolution_minutes"),
                avg_sla=Avg("sla_compliance_pct"),
                avg_csat=Avg("customer_satisfaction_avg"),
            )

            results.append({
                "agent_id": str(agent.id),
                "agent_name": agent.user.get_full_name(),
                "agent_email": agent.user.email,
                "team": agent.team.name if agent.team else None,
                "tickets_assigned": agg["total_assigned"] or 0,
                "tickets_resolved": agg["total_resolved"] or 0,
                "avg_first_response_min": round(agg["avg_frt"] or 0, 1),
                "avg_resolution_min": round(agg["avg_rt"] or 0, 1),
                "sla_compliance_pct": round(agg["avg_sla"] or 0, 1),
                "avg_csat": round(agg["avg_csat"] or 0, 2),
            })

        # Sort by tickets resolved descending
        results.sort(key=lambda x: x["tickets_resolved"], reverse=True)

        return {
            "agents": results,
            "total_agents": len(results),
        }

    @staticmethod
    def sla_compliance_report(date_from, date_to, filters=None):
        """
        Generate an SLA compliance report.
        """
        from apps.tickets.models import Ticket

        base_qs = Ticket.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )

        total = base_qs.count()
        response_breached = base_qs.filter(sla_response_breached=True).count()
        resolution_breached = base_qs.filter(sla_resolution_breached=True).count()
        any_breached = base_qs.filter(
            Q(sla_response_breached=True) | Q(sla_resolution_breached=True)
        ).count()

        daily_compliance = list(
            base_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total=Count("id"),
                breached=Count("id", filter=Q(
                    Q(sla_response_breached=True) | Q(sla_resolution_breached=True)
                )),
            )
            .order_by("date")
        )

        for entry in daily_compliance:
            entry["date"] = entry["date"].isoformat()
            entry["compliance_pct"] = round(
                (1 - entry["breached"] / entry["total"]) * 100, 1
            ) if entry["total"] > 0 else 100

        return {
            "total_tickets": total,
            "response_sla_breaches": response_breached,
            "resolution_sla_breaches": resolution_breached,
            "total_sla_breaches": any_breached,
            "overall_compliance_pct": round(
                (1 - any_breached / total) * 100, 1
            ) if total > 0 else 100,
            "daily_compliance": daily_compliance,
        }

    @staticmethod
    def customer_satisfaction_report(date_from, date_to, filters=None):
        """
        Generate a customer satisfaction report from chat ratings and ticket surveys.
        """
        from apps.live_chat.models import ChatSession

        rated_sessions = ChatSession.objects.filter(
            ended_at__date__gte=date_from,
            ended_at__date__lte=date_to,
            rating__isnull=False,
        )

        total_rated = rated_sessions.count()
        agg = rated_sessions.aggregate(avg_rating=Avg("rating"))

        rating_distribution = list(
            rated_sessions.values("rating")
            .annotate(count=Count("id"))
            .order_by("rating")
        )

        daily_csat = list(
            rated_sessions.annotate(date=TruncDate("ended_at"))
            .values("date")
            .annotate(avg_rating=Avg("rating"), count=Count("id"))
            .order_by("date")
        )

        for entry in daily_csat:
            entry["date"] = entry["date"].isoformat()
            entry["avg_rating"] = round(entry["avg_rating"], 2)

        return {
            "total_rated_sessions": total_rated,
            "average_rating": round(agg["avg_rating"] or 0, 2),
            "rating_distribution": rating_distribution,
            "daily_csat": daily_csat,
        }
