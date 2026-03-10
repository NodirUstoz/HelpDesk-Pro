"""
Admin configuration for knowledge base models.
"""
from django.contrib import admin

from .models import ArticleCategory, Article, ArticleFeedback


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title", "category", "author", "status", "is_featured",
        "is_internal", "view_count", "helpful_count", "published_at",
    )
    list_filter = ("status", "is_featured", "is_internal", "category")
    search_fields = ("title", "content", "excerpt")
    raw_id_fields = ("author",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("view_count", "helpful_count", "not_helpful_count", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("Content", {
            "fields": ("title", "slug", "content", "excerpt"),
        }),
        ("Classification", {
            "fields": ("category", "tags", "is_featured", "is_internal"),
        }),
        ("Publishing", {
            "fields": ("author", "status", "published_at"),
        }),
        ("Metrics", {
            "fields": ("view_count", "helpful_count", "not_helpful_count"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(ArticleFeedback)
class ArticleFeedbackAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "is_helpful", "created_at")
    list_filter = ("is_helpful",)
    search_fields = ("article__title", "comment")
    raw_id_fields = ("article", "user")
    readonly_fields = ("created_at",)
