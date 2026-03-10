"""
Admin configuration for extended agent models.
"""
from django.contrib import admin

from .models import AgentSkill, AgentAvailability, AgentPerformance


@admin.register(AgentSkill)
class AgentSkillAdmin(admin.ModelAdmin):
    list_display = ("agent", "name", "proficiency", "verified", "created_at")
    list_filter = ("proficiency", "verified")
    search_fields = ("name", "agent__user__email", "agent__user__first_name")
    raw_id_fields = ("agent",)


@admin.register(AgentAvailability)
class AgentAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("agent", "day_of_week", "start_time", "end_time", "is_active")
    list_filter = ("day_of_week", "is_active")
    raw_id_fields = ("agent",)


@admin.register(AgentPerformance)
class AgentPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        "agent", "date", "tickets_assigned", "tickets_resolved",
        "sla_compliance_pct", "customer_satisfaction_avg",
    )
    list_filter = ("date",)
    search_fields = ("agent__user__email", "agent__user__first_name")
    raw_id_fields = ("agent",)
    date_hierarchy = "date"
    readonly_fields = ("created_at",)
