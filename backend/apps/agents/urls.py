"""
URL patterns for the agents app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AgentSkillViewSet,
    AgentAvailabilityViewSet,
    AgentPerformanceViewSet,
)

router = DefaultRouter()
router.register(r"skills", AgentSkillViewSet, basename="agent-skill")
router.register(r"availability", AgentAvailabilityViewSet, basename="agent-availability")
router.register(r"performance", AgentPerformanceViewSet, basename="agent-performance")

urlpatterns = [
    path("", include(router.urls)),
]
