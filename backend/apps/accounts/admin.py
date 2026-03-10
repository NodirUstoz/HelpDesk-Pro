"""
Admin configuration for accounts models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Agent, Customer, Team


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_online", "is_active", "created_at")
    list_filter = ("role", "is_active", "is_online", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Role & Status", {"fields": ("role", "is_online", "last_activity")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "availability", "department", "current_ticket_count", "average_rating")
    list_filter = ("availability", "team")
    search_fields = ("user__email", "user__first_name", "department")
    raw_id_fields = ("user",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "is_vip", "total_tickets", "created_at")
    list_filter = ("is_vip",)
    search_fields = ("user__email", "user__first_name", "company")
    raw_id_fields = ("user",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "assignment_method", "is_active", "created_at")
    list_filter = ("is_active", "assignment_method")
    search_fields = ("name",)
