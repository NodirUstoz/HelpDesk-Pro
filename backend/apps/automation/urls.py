"""
URL patterns for the automation app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AutoRuleViewSet, TriggerViewSet, ActionViewSet

router = DefaultRouter()
router.register(r"rules", AutoRuleViewSet, basename="auto-rule")
router.register(r"triggers", TriggerViewSet, basename="auto-trigger")
router.register(r"actions", ActionViewSet, basename="auto-action")

urlpatterns = [
    path("", include(router.urls)),
]
