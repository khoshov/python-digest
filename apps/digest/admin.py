"""
Админка для приложения digest.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DigestRun, NewsSource, Article, GeneratedPost, Configuration, Keyword
)


@admin.register(DigestRun)
class DigestRunAdmin(admin.ModelAdmin):
    """Админка для запусков дайджеста."""
    
    list_display = [
        'id',
        'started_at',
        'status_display',
        'total_articles_collected',
        'total_articles_filtered', 
        'total_posts_created',
        'success_rate_display',
        'duration_display'
    ]
    list_filter = ['status', 'started_at']
    readonly_fields = [
        'started_at', 'finished_at', 'duration', 'success_rate'
    ]
    date_hierarchy = 'started_at'
    
    def status_display(self, obj):
        """Отображает статус с иконками."""
        status_icons = {
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'partial': '⚠️'
        }
        return f"{status_icons.get(obj.status, '❓')} {obj.get_status_display()}"
    status_display.short_description = 'Статус'
    
    def success_rate_display(self, obj):
        """Отображает процент успешности."""
        rate = obj.success_rate()
        color = 'green' if rate > 20 else 'orange' if rate > 5 else 'red'
        return format_html(
            '<span style="color: {};"><b>{:.1f}%</b></span>',
            color, rate
        )
    success_rate_display.short_description = 'Успешность'
    
    def duration_display(self, obj):
        """Отображает продолжительность выполнения."""
        duration = obj.duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}м {seconds}с"
        return "-"
    duration_display.short_description = 'Длительность'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    """Админка для источников новостей."""
    
    list_display = [
        'name',
        'source_type_display',
        'is_active_display',
        'priority',
        'last_collected',
        'articles_count',
        'success_rate_display'
    ]
    list_filter = ['source_type', 'is_active']
    list_editable = ['priority', 'is_active']
    
    def source_type_display(self, obj):
        """Отображает тип источника с иконкой."""
        icons = {
            'rss': '📰',
            'google': '🔍',
            'manual': '✍️'
        }
        return f"{icons.get(obj.source_type, '❓')} {obj.get_source_type_display()}"
    source_type_display.short_description = 'Тип'
    
    def is_active_display(self, obj):
        """Отображает активность с цветом."""
        if obj.is_active:
            return format_html('<span style="color: green;"><b>✅ Активен</b></span>')
        return format_html('<span style="color: red;"><b>❌ Неактивен</b></span>')
    is_active_display.short_description = 'Статус'
    
    def success_rate_display(self, obj):
        """Отображает процент успешности."""
        color = 'green' if obj.success_rate > 20 else 'orange' if obj.success_rate > 5 else 'red'
        return format_html(
            '<span style="color: {};"><b>{:.1f}%</b></span>',
            color, obj.success_rate
        )
    success_rate_display.short_description = 'Успешность'


class GeneratedPostInline(admin.TabularInline):
    """Inline для сгенерированных постов."""
    model = GeneratedPost
    extra = 0
    readonly_fields = ['platform', 'generated_at', 'is_published']
    can_delete = False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Админка для статей."""
    
    list_display = [
        'title_short',
        'source',
        'content_type_display',
        'interest_score_display',
        'is_relevant_display',
        'collected_at',
        'has_post'
    ]
    list_filter = ['content_type', 'is_relevant', 'source', 'digest_run']
    search_fields = ['title', 'summary']
    readonly_fields = ['collected_at']
    inlines = [GeneratedPostInline]
    
    def title_short(self, obj):
        """Сокращенный заголовок."""
        return obj.title[:60] + "..." if len(obj.title) > 60 else obj.title
    title_short.short_description = 'Заголовок'
    
    def content_type_display(self, obj):
        """Отображает тип контента с иконкой."""
        icons = {
            'tutorial': '📚',
            'news': '📰',
            'library': '🔧',
            'event': '📅',
            'opinion': '💭',
            'meme': '😂',
            'other': '❓'
        }
        return f"{icons.get(obj.content_type, '❓')} {obj.get_content_type_display()}"
    content_type_display.short_description = 'Тип'
    
    def interest_score_display(self, obj):
        """Отображает оценку интереса с цветом."""
        score = obj.interest_score
        if score >= 8:
            color = 'green'
            emoji = '🔥'
        elif score >= 5:
            color = 'orange'
            emoji = '⭐'
        else:
            color = 'red'
            emoji = '📉'
        
        return format_html(
            '<span style="color: {};"><b>{} {}/10</b></span>',
            color, emoji, score
        )
    interest_score_display.short_description = 'Оценка'
    
    def is_relevant_display(self, obj):
        """Отображает релевантность."""
        if obj.is_relevant:
            return format_html('<span style="color: green;"><b>✅ Релевантен</b></span>')
        return format_html('<span style="color: red;"><b>❌ Не релевантен</b></span>')
    is_relevant_display.short_description = 'Релевантность'
    
    def has_post(self, obj):
        """Показывает, есть ли сгенерированный пост."""
        return hasattr(obj, 'generated_post')
    has_post.boolean = True
    has_post.short_description = 'Есть пост'


@admin.register(GeneratedPost)
class GeneratedPostAdmin(admin.ModelAdmin):
    """Админка для сгенерированных постов."""
    
    list_display = [
        'article_title',
        'platform_display',
        'has_image',
        'is_published_display',
        'generated_at'
    ]
    list_filter = ['platform', 'is_published', 'generated_at']
    readonly_fields = ['generated_at']
    search_fields = ['article__title', 'post_content']
    
    def article_title(self, obj):
        """Заголовок статьи."""
        return obj.article.title[:50] + "..." if len(obj.article.title) > 50 else obj.article.title
    article_title.short_description = 'Статья'
    
    def platform_display(self, obj):
        """Отображает платформу с иконкой."""
        icons = {
            'telegram': '📱',
            'twitter': '🐦',
            'linkedin': '💼',
            'instagram': '📸',
            'general': '🌐'
        }
        return f"{icons.get(obj.platform, '❓')} {obj.get_platform_display()}"
    platform_display.short_description = 'Платформа'
    
    def has_image(self, obj):
        """Показывает, есть ли изображение."""
        return bool(obj.image_path)
    has_image.boolean = True
    has_image.short_description = 'Изображение'
    
    def is_published_display(self, obj):
        """Отображает статус публикации."""
        if obj.is_published:
            return format_html('<span style="color: green;"><b>✅ Опубликован</b></span>')
        return format_html('<span style="color: orange;"><b>📝 Черновик</b></span>')
    is_published_display.short_description = 'Статус'


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    """Админка для конфигураций."""
    
    list_display = [
        'name',
        'is_active_display',
        'enable_google_news',
        'enable_rss_news',
        'generate_images',
        'enable_email_sending',
        'updated_at'
    ]
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_active_display(self, obj):
        """Отображает активность конфигурации."""
        if obj.is_active:
            return format_html('<span style="color: green;"><b>✅ Активная</b></span>')
        return format_html('<span style="color: gray;"><b>⚪ Неактивная</b></span>')
    is_active_display.short_description = 'Статус'


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    """Админка для ключевых слов."""
    
    list_display = [
        'keyword',
        'is_active_display',
        'priority',
        'created_at'
    ]
    list_editable = ['is_active', 'priority']
    list_filter = ['is_active']
    search_fields = ['keyword']
    
    def is_active_display(self, obj):
        """Отображает активность ключевого слова."""
        if obj.is_active:
            return format_html('<span style="color: green;"><b>✅ Активно</b></span>')
        return format_html('<span style="color: red;"><b>❌ Неактивно</b></span>')
    is_active_display.short_description = 'Статус'
