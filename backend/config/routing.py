"""
WebSocket URL routing for HelpDesk Pro.
"""
from django.urls import re_path

from apps.live_chat.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<session_id>[0-9a-f-]+)/$", ChatConsumer.as_asgi()),
]
