"""
Custom permissions for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsAgent(BasePermission):
    """Allow access only to agent users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_agent or request.user.is_admin)
        )


class IsCustomer(BasePermission):
    """Allow access only to customer users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_customer
        )


class IsAdminOrAgent(BasePermission):
    """Allow access to admin or agent users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_agent)
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access to the object owner or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        # Check common owner field patterns
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "created_by"):
            return obj.created_by == request.user
        if hasattr(obj, "customer"):
            return obj.customer.user == request.user
        return False


class IsAgentOrReadOnly(BasePermission):
    """Allow agents full access; others read-only."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_agent or request.user.is_admin)
        )
