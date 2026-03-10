"""
Custom exception handling for HelpDesk Pro API.
"""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error response format.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "status_code": response.status_code,
            "error": _get_error_type(response.status_code),
            "detail": response.data,
        }

        # Flatten single-field errors
        if isinstance(response.data, dict) and "detail" in response.data:
            error_payload["detail"] = response.data["detail"]

        response.data = error_payload
    else:
        # Unhandled exception: log and return 500
        logger.exception(
            "Unhandled exception in %s",
            context.get("view", "unknown"),
            exc_info=exc,
        )
        response = Response(
            {
                "status_code": 500,
                "error": "internal_server_error",
                "detail": "An unexpected error occurred. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_type(status_code):
    """Map HTTP status codes to human-readable error types."""
    error_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "unprocessable_entity",
        429: "too_many_requests",
        500: "internal_server_error",
    }
    return error_map.get(status_code, "error")


class TicketClosedError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This ticket is closed and cannot be modified."
    default_code = "ticket_closed"


class SLABreachError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "SLA policy has been breached."
    default_code = "sla_breach"


class ChatSessionEndedError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This chat session has ended."
    default_code = "chat_session_ended"


class AssignmentError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Unable to assign ticket to the specified agent."
    default_code = "assignment_error"
