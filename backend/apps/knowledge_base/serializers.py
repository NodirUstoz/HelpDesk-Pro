"""
Serializers for the knowledge base models.
"""
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import ArticleCategory, Article, ArticleFeedback


class ArticleCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = ArticleCategory
        fields = [
            "id", "name", "slug", "description", "icon", "parent",
            "order", "is_active", "article_count", "children",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return ArticleCategorySerializer(children, many=True).data


class ArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for article listing."""

    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    helpfulness_ratio = serializers.FloatField(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "excerpt", "category", "category_name",
            "author", "author_name", "status", "tags",
            "is_featured", "is_internal",
            "view_count", "helpful_count", "not_helpful_count",
            "helpfulness_ratio", "published_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "view_count", "helpful_count", "not_helpful_count"]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Full article serializer with content."""

    author_detail = UserSerializer(source="author", read_only=True)
    category_detail = ArticleCategorySerializer(source="category", read_only=True)
    helpfulness_ratio = serializers.FloatField(read_only=True)
    feedback_summary = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "content", "excerpt",
            "category", "category_detail",
            "author", "author_detail",
            "status", "tags", "is_featured", "is_internal",
            "view_count", "helpful_count", "not_helpful_count",
            "helpfulness_ratio", "feedback_summary",
            "published_at", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "view_count", "helpful_count",
            "not_helpful_count", "created_at", "updated_at",
        ]

    def get_feedback_summary(self, obj):
        recent_feedback = obj.feedback.order_by("-created_at")[:5]
        return ArticleFeedbackSerializer(recent_feedback, many=True).data

    def update(self, instance, validated_data):
        # Auto-set published_at when status changes to published
        if (
            validated_data.get("status") == Article.Status.PUBLISHED
            and instance.status != Article.Status.PUBLISHED
        ):
            validated_data["published_at"] = timezone.now()
        return super().update(instance, validated_data)


class ArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "title", "content", "excerpt", "category",
            "status", "tags", "is_featured", "is_internal",
        ]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        if validated_data.get("status") == Article.Status.PUBLISHED:
            validated_data["published_at"] = timezone.now()
        return super().create(validated_data)


class ArticleFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True, default="Anonymous")

    class Meta:
        model = ArticleFeedback
        fields = ["id", "article", "user", "user_name", "is_helpful", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        feedback = super().create(validated_data)

        # Update article counters
        article = feedback.article
        if feedback.is_helpful:
            article.helpful_count += 1
        else:
            article.not_helpful_count += 1
        article.save(update_fields=["helpful_count", "not_helpful_count"])

        return feedback
