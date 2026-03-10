"""
URL patterns for the SLA app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SLAPolicyViewSet, SLARuleViewSet, EscalationViewSet

router = DefaultRouter()
router.register(r"policies", SLAPolicyViewSet, basename="sla-policy")
router.register(r"rules", SLARuleViewSet, basename="sla-rule")
router.register(r"escalations", EscalationViewSet, basename="sla-escalation")

urlpatterns = [
    path("", include(router.urls)),
]
