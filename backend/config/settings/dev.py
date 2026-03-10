"""
Development settings for HelpDesk Pro.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable throttling in development
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405

# CORS: allow all in dev
CORS_ALLOW_ALL_ORIGINS = True

# Shorter token lifetime for dev testing
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(hours=24)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=30)  # noqa: F405

# Use whitenoise in dev without manifest (avoids missing file errors)
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
