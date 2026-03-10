"""
Root URL configuration for HelpDesk Pro.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/tickets/", include("apps.tickets.urls")),
    path("api/chat/", include("apps.live_chat.urls")),
    path("api/kb/", include("apps.knowledge_base.urls")),
    path("api/sla/", include("apps.sla.urls")),
    path("api/canned-responses/", include("apps.canned_responses.urls")),
    path("api/satisfaction/", include("apps.satisfaction.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
