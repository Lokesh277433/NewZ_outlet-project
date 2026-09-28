from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=60)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EditorialSettings(models.Model):
    auto_approve_staff = models.BooleanField(
        default=False,
        help_text='When on, staff submissions publish immediately without review.',
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )

    class Meta:
        verbose_name = 'editorial settings'
        verbose_name_plural = 'editorial settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Editorial settings'


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=120)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('news:section', kwargs={'slug': self.slug})


class WireStory(models.Model):
    """A short, on-site preview of a headline supplied by GNews."""

    title = models.CharField(max_length=500)
    source_url = models.URLField(max_length=1000, unique=True)
    source_name = models.CharField(max_length=150, default='Wire')
    excerpt = models.TextField(blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    source_published_at = models.CharField(max_length=100, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fetched_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:wire_story', kwargs={'pk': self.pk})


class Article(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_REVIEW = 'review'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_REVIEW, 'Pending review'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=280)
    kicker = models.CharField(max_length=200, blank=True)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    hero_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='articles'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles')
    is_breaking = models.BooleanField(default=False)
    is_featured = models.BooleanField(
        default=False,
        help_text='Pinned to the homepage hero. Only one article should be featured.',
    )
    review_note = models.TextField(blank=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'article'
            slug = base
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        if self.is_featured and self.status == self.STATUS_PUBLISHED:
            Article.objects.filter(is_featured=True).exclude(pk=self.pk).update(is_featured=False)

    def get_absolute_url(self):
        return reverse('news:article', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return self.status == self.STATUS_PUBLISHED


class Comment(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user} on {self.article}'


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
    )
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='bookmarks',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'article']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} bookmarked {self.article}'
