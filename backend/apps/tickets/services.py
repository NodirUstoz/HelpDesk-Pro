"""
Business logic services for ticket operations.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Agent, Team, User
from apps.sla.models import SLAPolicy
from .models import Ticket, TicketMessage, TicketStatus

logger = logging.getLogger(__name__)


class TicketService:
    """Service class for ticket business operations."""

    @staticmethod
    def assign_ticket(ticket, agent_id=None, team_id=None):
        """
        Assign a ticket to an agent or team.
        If team is specified without agent, auto-assign based on team rules.
        """
        if agent_id:
            try:
                agent_user = User.objects.get(id=agent_id, role=User.Role.AGENT)
                ticket.assigned_agent = agent_user
                # Update agent ticket count
                if hasattr(agent_user, "agent_profile"):
                    agent_user.agent_profile.current_ticket_count += 1
                    agent_user.agent_profile.save(update_fields=["current_ticket_count"])
                logger.info("Ticket %s assigned to agent %s", ticket.ticket_number, agent_user.email)
            except User.DoesNotExist:
                raise ValueError(f"Agent with ID {agent_id} not found.")

        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                ticket.assigned_team = team
                # Auto-assign if no agent specified
                if not agent_id:
                    auto_agent = TicketService._auto_assign_from_team(team)
                    if auto_agent:
                        ticket.assigned_agent = auto_agent.user
                        auto_agent.current_ticket_count += 1
                        auto_agent.save(update_fields=["current_ticket_count"])
            except Team.DoesNotExist:
                raise ValueError(f"Team with ID {team_id} not found.")

        ticket.save()
        return ticket

    @staticmethod
    def _auto_assign_from_team(team):
        """Auto-assign to an available agent in the team based on assignment method."""
        available_agents = Agent.objects.filter(
            team=team,
            availability__in=[Agent.Availability.ONLINE, Agent.Availability.AWAY],
        )

        if not available_agents.exists():
            return None

        if team.assignment_method == Team.AssignmentMethod.LOAD_BALANCED:
            return available_agents.order_by("current_ticket_count").first()
        elif team.assignment_method == Team.AssignmentMethod.ROUND_ROBIN:
            # Pick agent who was assigned longest ago
            return available_agents.order_by("updated_at").first()
        return None

    @staticmethod
    def close_ticket(ticket, resolved_by=None):
        """Close a ticket and update metrics."""
        closed_status = TicketStatus.objects.filter(is_closed=True).first()
        if closed_status:
            ticket.status = closed_status
        ticket.resolved_at = timezone.now()
        ticket.save()

        # Update agent metrics
        if ticket.assigned_agent and hasattr(ticket.assigned_agent, "agent_profile"):
            agent_profile = ticket.assigned_agent.agent_profile
            agent_profile.current_ticket_count = max(0, agent_profile.current_ticket_count - 1)
            agent_profile.total_tickets_resolved += 1
            agent_profile.save(update_fields=["current_ticket_count", "total_tickets_resolved"])

        # Update customer metrics
        if hasattr(ticket.customer, "customer_profile"):
            customer_profile = ticket.customer.customer_profile
            customer_profile.total_tickets = Ticket.objects.filter(
                customer=ticket.customer
            ).count()
            customer_profile.save(update_fields=["total_tickets"])

        # Create system message
        TicketMessage.objects.create(
            ticket=ticket,
            sender=resolved_by,
            body="Ticket has been closed.",
            message_type=TicketMessage.MessageType.SYSTEM,
        )

        logger.info("Ticket %s closed", ticket.ticket_number)
        return ticket

    @staticmethod
    def apply_sla_policy(ticket):
        """
        Apply the appropriate SLA policy to a ticket.
        Searches for matching policies by priority, then applies default.
        """
        policy = None
        if ticket.priority:
            policy = SLAPolicy.objects.filter(
                is_active=True,
                rules__priority=ticket.priority,
            ).first()

        if not policy:
            policy = SLAPolicy.objects.filter(is_active=True, is_default=True).first()

        if policy:
            ticket.sla_policy = policy
            rule = policy.rules.filter(priority=ticket.priority).first()
            if rule:
                now = timezone.now()
                ticket.sla_response_due = now + timedelta(minutes=rule.response_time_minutes)
                ticket.sla_resolution_due = now + timedelta(minutes=rule.resolution_time_minutes)
            else:
                now = timezone.now()
                ticket.sla_response_due = now + timedelta(
                    minutes=getattr(settings, "DEFAULT_SLA_RESPONSE_TIME", 60)
                )
                ticket.sla_resolution_due = now + timedelta(
                    minutes=getattr(settings, "DEFAULT_SLA_RESOLUTION_TIME", 480)
                )
            ticket.save()

        return ticket

    @staticmethod
    def record_first_response(ticket):
        """Record the first agent response time for SLA tracking."""
        if not ticket.first_response_at:
            ticket.first_response_at = timezone.now()
            if ticket.sla_response_due and ticket.first_response_at > ticket.sla_response_due:
                ticket.sla_response_breached = True
            ticket.save(update_fields=["first_response_at", "sla_response_breached"])

    @staticmethod
    def get_filtered_tickets(user, filters=None):
        """
        Get tickets filtered by user role and optional filters.
        Customers see only their own tickets.
        Agents see their assigned tickets plus unassigned ones.
        Admins see all tickets.
        """
        queryset = Ticket.objects.select_related(
            "customer", "assigned_agent", "priority", "status", "assigned_team"
        ).prefetch_related("tags")

        if user.is_customer:
            queryset = queryset.filter(customer=user)
        elif user.is_agent:
            queryset = queryset.filter(
                Q(assigned_agent=user) | Q(assigned_agent__isnull=True)
            )
        # Admins see all

        return queryset
