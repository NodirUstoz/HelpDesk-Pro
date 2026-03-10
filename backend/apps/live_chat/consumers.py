"""
WebSocket consumers for real-time live chat.
"""
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebSocketConsumer
from django.utils import timezone

from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebSocketConsumer):
    """
    WebSocket consumer handling real-time chat communication.
    Supports text messages, typing indicators, read receipts, and agent assignment.
    """

    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"chat_{self.session_id}"
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return

        # Verify user belongs to this chat session
        session = await self.get_session()
        if not session:
            await self.close(code=4004)
            return

        is_participant = await self.is_session_participant(session)
        if not is_participant:
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        # Notify room that user connected
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": str(self.user.id),
                "user_name": self.user.get_full_name(),
                "role": self.user.role,
            },
        )

        # If agent joining, update session
        if self.user.is_agent or self.user.is_admin:
            await self.handle_agent_join(session)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

        # Notify room of disconnect
        if hasattr(self, "user") and self.user and not self.user.is_anonymous:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_left",
                    "user_id": str(self.user.id),
                    "user_name": self.user.get_full_name(),
                },
            )

    async def receive_json(self, content, **kwargs):
        """Handle incoming WebSocket messages."""
        msg_type = content.get("type", "chat_message")

        handlers = {
            "chat_message": self.handle_chat_message,
            "typing": self.handle_typing,
            "read_receipt": self.handle_read_receipt,
            "end_chat": self.handle_end_chat,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(content)
        else:
            await self.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})

    async def handle_chat_message(self, content):
        """Save message to DB and broadcast to room."""
        message_text = content.get("message", "").strip()
        message_type = content.get("message_type", ChatMessage.MessageType.TEXT)
        file_url = content.get("file_url", "")

        if not message_text and not file_url:
            return

        # Persist message
        chat_message = await self.save_message(message_text, message_type, file_url)

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message_broadcast",
                "message_id": str(chat_message.id),
                "sender_id": str(self.user.id),
                "sender_name": self.user.get_full_name(),
                "sender_role": self.user.role,
                "content": message_text,
                "message_type": message_type,
                "file_url": file_url,
                "timestamp": chat_message.created_at.isoformat(),
            },
        )

    async def handle_typing(self, content):
        """Broadcast typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": str(self.user.id),
                "user_name": self.user.get_full_name(),
                "is_typing": content.get("is_typing", True),
            },
        )

    async def handle_read_receipt(self, content):
        """Mark messages as read."""
        message_ids = content.get("message_ids", [])
        if message_ids:
            await self.mark_messages_read(message_ids)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "messages_read",
                    "user_id": str(self.user.id),
                    "message_ids": message_ids,
                },
            )

    async def handle_end_chat(self, content):
        """End the chat session."""
        await self.close_session()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_ended",
                "ended_by": str(self.user.id),
                "ended_by_name": self.user.get_full_name(),
            },
        )

    # ------------------------------------------------------------------
    # Broadcast handlers (called by channel_layer.group_send)
    # ------------------------------------------------------------------

    async def chat_message_broadcast(self, event):
        await self.send_json({
            "type": "chat_message",
            "message_id": event["message_id"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "sender_role": event["sender_role"],
            "content": event["content"],
            "message_type": event["message_type"],
            "file_url": event["file_url"],
            "timestamp": event["timestamp"],
        })

    async def typing_indicator(self, event):
        # Don't echo typing back to the sender
        if event["user_id"] != str(self.user.id):
            await self.send_json({
                "type": "typing",
                "user_id": event["user_id"],
                "user_name": event["user_name"],
                "is_typing": event["is_typing"],
            })

    async def messages_read(self, event):
        await self.send_json({
            "type": "read_receipt",
            "user_id": event["user_id"],
            "message_ids": event["message_ids"],
        })

    async def user_joined(self, event):
        await self.send_json({
            "type": "user_joined",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
            "role": event["role"],
        })

    async def user_left(self, event):
        await self.send_json({
            "type": "user_left",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
        })

    async def chat_ended(self, event):
        await self.send_json({
            "type": "chat_ended",
            "ended_by": event["ended_by"],
            "ended_by_name": event["ended_by_name"],
        })

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_session(self):
        try:
            return ChatSession.objects.get(id=self.session_id)
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def is_session_participant(self, session):
        user = self.user
        if user.is_admin:
            return True
        return (
            session.customer_id == user.id
            or session.agent_id == user.id
            or (user.is_agent and session.agent is None)
        )

    @database_sync_to_async
    def handle_agent_join(self, session):
        if session.status == ChatSession.Status.WAITING:
            session.agent = self.user
            session.status = ChatSession.Status.ACTIVE
            session.agent_joined_at = timezone.now()
            session.save(update_fields=["agent", "status", "agent_joined_at"])

            # Update agent chat count
            if hasattr(self.user, "agent_profile"):
                profile = self.user.agent_profile
                profile.current_chat_count += 1
                profile.save(update_fields=["current_chat_count"])

            # Create system message
            ChatMessage.objects.create(
                session=session,
                sender=None,
                content=f"{self.user.get_full_name()} has joined the chat.",
                message_type=ChatMessage.MessageType.SYSTEM,
            )

    @database_sync_to_async
    def save_message(self, text, message_type, file_url):
        return ChatMessage.objects.create(
            session_id=self.session_id,
            sender=self.user,
            content=text,
            message_type=message_type,
            file_url=file_url,
        )

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        ChatMessage.objects.filter(
            id__in=message_ids,
            session_id=self.session_id,
        ).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def close_session(self):
        session = ChatSession.objects.get(id=self.session_id)
        session.status = ChatSession.Status.CLOSED
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])

        # Update agent chat count
        if session.agent and hasattr(session.agent, "agent_profile"):
            profile = session.agent.agent_profile
            profile.current_chat_count = max(0, profile.current_chat_count - 1)
            profile.save(update_fields=["current_chat_count"])

        # Create system message
        ChatMessage.objects.create(
            session=session,
            sender=None,
            content="Chat session has ended.",
            message_type=ChatMessage.MessageType.SYSTEM,
        )
