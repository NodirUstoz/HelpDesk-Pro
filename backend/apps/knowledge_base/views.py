"""
Views for knowledge base articles and categories.
"""
from django.db.models import Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrAgent, IsAgentOrReadOnly
from .models import ArticleCategory, Article, ArticleFeedback
from .serializers import (
    ArticleCategorySerializer,
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer,
    ArticleFeedbackSerializer,
)


class ArticleCategoryViewSet(viewsets.ModelViewSet):
    """Manage knowledge base categories."""

    serializer_class = ArticleCategorySerializer
    permission_classes = [IsAuthenticated, IsAgentOrReadOnly]
    filterset_fields = ["is_active", "parent"]
    search_fields = ["name"]

    def get_queryset(self):
        qs = ArticleCategory.objects.annotate(
            article_count=Count(
                "articles",
                filter=Q(articles__status=Article.Status.PUBLISHED),
            )
        )
        # Only root categories by default
        if self.request.query_params.get("root_only", "false").lower() == "true":
            qs = qs.filter(parent__isnull=True)
        return qs


class ArticleViewSet(viewsets.ModelViewSet):
    """
    CRUD for knowledge base articles.
    Public users see published non-internal articles.
    Agents see all published articles including internal.
    Admins see everything.
    """

    permission_classes = [IsAuthenticated, IsAgentOrReadOnly]
    filterset_fields = ["category", "status", "is_featured", "is_internal"]
    search_fields = ["title", "content", "excerpt", "tags"]
    ordering_fields = ["created_at", "updated_at", "view_count", "helpful_count"]
    ordering = ["-updated_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ArticleCreateSerializer
        if self.action == "list":
            return ArticleListSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        qs = Article.objects.select_related("category", "author").all()
        user = self.request.user

        if user.is_admin:
            return qs
        elif user.is_agent:
            return qs.filter(status=Article.Status.PUBLISHED)
        else:
            # Customers see only public published articles
            return qs.filter(
                status=Article.Status.PUBLISHED,
                is_internal=False,
            )

    def retrieve(self, request, *args, **kwargs):
        """Increment view count on article retrieval."""
        instance = self.get_object()
        Article.objects.filter(pk=instance.pk).update(
            view_count=instance.view_count + 1
        )
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Full-text search across articles."""
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"error": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(tags__icontains=query)
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ArticleListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Return featured articles."""
        qs = self.get_queryset().filter(is_featured=True)
        serializer = ArticleListSerializer(qs[:10], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Return most-viewed articles."""
        qs = self.get_queryset().order_by("-view_count")
        serializer = ArticleListSerializer(qs[:10], many=True)
        return Response(serializer.data)


class ArticleFeedbackViewSet(viewsets.ModelViewSet):
    """Submit and manage article feedback."""

    serializer_class = ArticleFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ArticleFeedback.objects.select_related("article", "user").all()
        article_id = self.request.query_params.get("article_id")
        if article_id:
            qs = qs.filter(article_id=article_id)
        if self.request.user.is_customer:
            qs = qs.filter(user=self.request.user)
        return qs
