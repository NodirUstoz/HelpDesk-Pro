"""
Knowledge base models: ArticleCategory, Article, ArticleFeedback.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class ArticleCategory(models.Model):
    """
    Hierarchical categories for organizing knowledge base articles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(
        max_length=50, blank=True, default="folder",
        help_text="Icon identifier (e.g., 'folder', 'settings', 'billing')",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="children",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Article Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def article_count(self):
        return self.articles.filter(status=Article.Status.PUBLISHED).count()


class Article(models.Model):
    """
    Knowledge base article with markdown content and versioning support.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In Review"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    content = models.TextField(help_text="Markdown content")
    excerpt = models.TextField(
        max_length=500, blank=True, default="",
        help_text="Short summary shown in search results",
    )

    category = models.ForeignKey(
        ArticleCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="articles",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="kb_articles",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT,
    )

    tags = models.JSONField(default=list, blank=True, help_text="List of tag strings")
    is_featured = models.BooleanField(default=False)
    is_internal = models.BooleanField(
        default=False,
        help_text="Internal articles are only visible to agents",
    )

    view_count = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-view_count"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def helpfulness_ratio(self):
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return round(self.helpful_count / total * 100, 1)


class ArticleFeedback(models.Model):
    """
    User feedback on knowledge base articles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="feedback",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    is_helpful = models.BooleanField()
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("article", "user")]

    def __str__(self):
        verdict = "Helpful" if self.is_helpful else "Not helpful"
        return f"{verdict} - {self.article.title}"
