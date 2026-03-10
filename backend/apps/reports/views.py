"""
Views for generating and retrieving reports.
"""
from datetime import datetime, timedelta

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsAdminOrAgent
from .models import Report, ScheduledReport
from .services import ReportService


class ReportViewSet(viewsets.ViewSet):
    """
    Generate and retrieve reports.
    """

    permission_classes = [IsAuthenticated, IsAdminOrAgent]

    def _parse_dates(self, request):
        """Parse date_from and date_to from query params, with defaults."""
        date_to = request.query_params.get("date_to")
        date_from = request.query_params.get("date_from")

        if date_to:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        else:
            date_to = datetime.now().date()

        if date_from:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        else:
            date_from = date_to - timedelta(days=30)

        return date_from, date_to

    def _get_filters(self, request):
        """Extract optional filter params."""
        filters = {}
        team_id = request.query_params.get("team_id")
        if team_id:
            filters["team_id"] = team_id
        return filters

    @action(detail=False, methods=["get"])
    def ticket_summary(self, request):
        """Generate a ticket summary report."""
        date_from, date_to = self._parse_dates(request)
        filters = self._get_filters(request)
        data = ReportService.ticket_summary(date_from, date_to, filters)
        return Response({
            "report_type": "ticket_summary",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data": data,
        })

    @action(detail=False, methods=["get"])
    def agent_performance(self, request):
        """Generate an agent performance report."""
        date_from, date_to = self._parse_dates(request)
        filters = self._get_filters(request)
        data = ReportService.agent_performance_report(date_from, date_to, filters)
        return Response({
            "report_type": "agent_performance",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data": data,
        })

    @action(detail=False, methods=["get"])
    def sla_compliance(self, request):
        """Generate an SLA compliance report."""
        date_from, date_to = self._parse_dates(request)
        filters = self._get_filters(request)
        data = ReportService.sla_compliance_report(date_from, date_to, filters)
        return Response({
            "report_type": "sla_compliance",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data": data,
        })

    @action(detail=False, methods=["get"])
    def customer_satisfaction(self, request):
        """Generate a customer satisfaction report."""
        date_from, date_to = self._parse_dates(request)
        filters = self._get_filters(request)
        data = ReportService.customer_satisfaction_report(date_from, date_to, filters)
        return Response({
            "report_type": "customer_satisfaction",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data": data,
        })

    @action(detail=False, methods=["post"])
    def save_report(self, request):
        """Save a generated report snapshot."""
        report = Report.objects.create(
            name=request.data.get("name", "Untitled Report"),
            report_type=request.data.get("report_type"),
            generated_by=request.user,
            date_from=request.data.get("date_from"),
            date_to=request.data.get("date_to"),
            filters=request.data.get("filters", {}),
            data=request.data.get("data", {}),
        )
        return Response({
            "id": str(report.id),
            "name": report.name,
            "message": "Report saved successfully.",
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def saved_reports(self, request):
        """List saved report snapshots."""
        reports = Report.objects.filter(
            generated_by=request.user
        ).values(
            "id", "name", "report_type", "date_from", "date_to", "created_at"
        ).order_by("-created_at")
        return Response(list(reports))

    @action(detail=False, methods=["get"], url_path="saved_reports/(?P<report_id>[0-9a-f-]+)")
    def get_saved_report(self, request, report_id=None):
        """Retrieve a specific saved report."""
        try:
            report = Report.objects.get(id=report_id, generated_by=request.user)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "id": str(report.id),
            "name": report.name,
            "report_type": report.report_type,
            "date_from": report.date_from.isoformat(),
            "date_to": report.date_to.isoformat(),
            "filters": report.filters,
            "data": report.data,
            "created_at": report.created_at.isoformat(),
        })
