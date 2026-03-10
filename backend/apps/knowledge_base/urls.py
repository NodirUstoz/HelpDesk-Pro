"""
URL patterns for the knowledge base app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ArticleCategoryViewSet, ArticleViewSet, ArticleFeedbackViewSet

router = DefaultRouter()
router.register(r"categories", ArticleCategoryViewSet, basename="kb-category")
router.register(r"articles", ArticleViewSet, basename="kb-article")
router.register(r"feedback", ArticleFeedbackViewSet, basename="kb-feedback")

urlpatterns = [
    path("", include(router.urls)),
]
