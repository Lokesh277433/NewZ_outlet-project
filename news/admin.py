from django.contrib import admin

from .models import Article, Bookmark, Category, Comment, EditorialSettings, Tag, WireStory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'author', 'status',
        'is_breaking', 'is_featured', 'published_at',
    ]
    list_filter = ['status', 'category', 'is_breaking', 'is_featured', 'tags']
    filter_horizontal = ['tags']
    search_fields = ['title', 'kicker', 'body']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'published_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['body', 'user__email', 'user__username']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(EditorialSettings)
class EditorialSettingsAdmin(admin.ModelAdmin):
    list_display = ['auto_approve_staff', 'updated_at', 'updated_by']


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'created_at']
    raw_id_fields = ['user', 'article']


@admin.register(WireStory)
class WireStoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'source_name', 'source_published_at', 'fetched_at']
    search_fields = ['title', 'source_name']
    readonly_fields = ['fetched_at']
