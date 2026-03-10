"""
Admin configuration for ticket models.
"""
from django.contrib import admin

from .models import Ticket, TicketMessage, TicketAttachment, TicketTag, TicketPriority, TicketStatus


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number", "subject", "customer", "assigned_agent",
        "priority", "status", "channel", "is_escalated", "created_at",
    )
    list_filter = ("status", "priority", "channel", "is_escalated", "is_spam")
    search_fields = ("ticket_number", "subject", "description", "customer__email")
    raw_id_fields = ("customer", "assigned_agent", "assigned_team")
    readonly_fields = ("ticket_number", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 30

    fieldsets = (
        ("Ticket Info", {
            "fields": (
                "ticket_number", "subject", "description", "channel",
            ),
        }),
        ("Assignment", {
            "fields": ("customer", "assigned_agent", "assigned_team"),
        }),
        ("Classification", {
            "fields": ("priority", "status", "tags", "is_escalated", "is_spam"),
        }),
        ("SLA Tracking", {
            "fields": (
                "sla_policy", "first_response_at", "resolved_at",
                "sla_response_due", "sla_resolution_due",
                "sla_response_breached", "sla_resolution_breached",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "sender", "message_type", "is_customer_visible", "created_at")
    list_filter = ("message_type", "is_customer_visible")
    search_fields = ("body", "ticket__ticket_number")
    raw_id_fields = ("ticket", "sender")
    readonly_fields = ("created_at",)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "message", "file_size", "content_type", "uploaded_at")
    search_fields = ("filename",)
    raw_id_fields = ("message",)
    readonly_fields = ("uploaded_at",)


@admin.register(TicketTag)
class TicketTagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(TicketPriority)
class TicketPriorityAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "color", "is_active")
    list_filter = ("is_active",)
    ordering = ("level",)


@admin.register(TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color", "is_closed", "is_default", "order")
    list_filter = ("is_closed", "is_default")
    ordering = ("order",)
