"""
URL patterns for the live chat app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import ChatSessionViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register(r"sessions", ChatSessionViewSet, basename="chat-session")

# Nested router: /api/chat/sessions/<session_pk>/messages/
sessions_router = nested_routers.NestedDefaultRouter(router, r"sessions", lookup="session")
sessions_router.register(r"messages", ChatMessageViewSet, basename="chat-message")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(sessions_router.urls)),
]
