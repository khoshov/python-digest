"""
Административная панель для приложения digest.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages

from .models import (
    DigestRun,
    ArticleSource,
    Article,
    GeneratedPost,
    Project,
    Keyword,
)
from .services.pipeline_runner import run_pipeline_for_project


# Inline админки для связанных моделей
class KeywordInline(admin.TabularInline):
    """Inline для ключевых слов Google CSE проекта."""
    model = Keyword
    extra = 1
    fields = ('keyword', 'priority', 'is_active')
    verbose_name = "Ключевое слово (для Google CSE)"
    verbose_name_plural = "Ключевые слова (для Google CSE)"
    classes = ('collapse',)


class ArticleSourceInline(admin.TabularInline):
    """Inline для RSS источников проекта."""
    model = ArticleSource
    extra = 1
    fields = ('name', 'url', 'priority', 'is_active')
    show_change_link = True
    verbose_name = "RSS источник"
    verbose_name_plural = "RSS источники"
    classes = ('collapse',)


class ArticleInline(admin.TabularInline):
    """Inline для статей в запуске дайджеста."""
    model = Article
    extra = 0
    fields = ('title', 'interest_score', 'is_relevant', 'content_type', 'source')
    readonly_fields = ('title', 'interest_score', 'is_relevant', 'content_type', 'source')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Административная панель для проектов."""

    list_display = (
        'name',
        'is_active_badge',
        'sources_count',
        'keywords_count',
        'rss_hours_period',
        'max_final_posts',
        'updated_at',
    )
    list_filter = ('is_active', 'enable_rss_news', 'enable_google_news', 'generate_images')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'is_active')
        }),
        ('Настройки сбора', {
            'fields': (
                'rss_hours_period',
                'max_articles_per_source',
                'max_final_posts',
            ),
            'description': 'Общие параметры сбора и обработки статей'
        }),
        ('Функции', {
            'fields': (
                'enable_rss_news',
                'enable_google_news',
                'generate_images',
                'enable_email_sending',
            ),
            'description': 'RSS источники настраиваются ниже. Google CSE - через ключевые слова.'
        }),
        ('Промпты для фильтра', {
            'classes': ('collapse',),
            'fields': ('filter_system_prompt', 'filter_user_prompt')
        }),
        ('Промпты для копирайтера', {
            'classes': ('collapse',),
            'fields': ('copywriter_system_prompt', 'copywriter_user_prompt')
        }),
        ('Системная информация', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    inlines = [KeywordInline, ArticleSourceInline]
    actions = ['run_digest_action', 'activate_project']

    def is_active_badge(self, obj):
        """Отображает значок активности."""
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Активный</span>')
        return format_html('<span style="color: gray;">❌ Неактивный</span>')
    is_active_badge.short_description = 'Статус'

    def sources_count(self, obj):
        """Количество RSS источников."""
        count = obj.sources.count()
        active_count = obj.sources.filter(is_active=True).count()
        return format_html('{} <span style="color: gray;">(активных: {})</span>', count, active_count)
    sources_count.short_description = 'RSS источников'

    def keywords_count(self, obj):
        """Количество ключевых слов для Google CSE."""
        count = obj.keywords.count()
        active_count = obj.keywords.filter(is_active=True).count()
        return format_html('{} <span style="color: gray;">(активных: {})</span>', count, active_count)
    keywords_count.short_description = 'Ключевых слов (CSE)'

    @admin.action(description='🚀 Запустить дайджест для выбранных проектов')
    def run_digest_action(self, request, queryset):
        """Запускает дайджест для выбранных проектов."""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Можно запустить дайджест только для одного проекта за раз",
                level=messages.WARNING
            )
            return

        project = queryset.first()

        try:
            self.message_user(
                request,
                f"🚀 Запуск дайджеста для проекта '{project.name}'...",
                level=messages.INFO
            )

            result = run_pipeline_for_project(project.id)

            if result['success']:
                self.message_user(
                    request,
                    f"✅ Дайджест успешно создан! Создано постов: {result['total_posts']}",
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"❌ Ошибка при создании дайджеста: {result['error']}",
                    level=messages.ERROR
                )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Ошибка: {str(e)}",
                level=messages.ERROR
            )

    @admin.action(description='✅ Активировать выбранные проекты')
    def activate_project(self, request, queryset):
        """Активирует выбранный проект (деактивирует остальные)."""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Можно активировать только один проект",
                level=messages.WARNING
            )
            return

        project = queryset.first()
        Project.objects.filter(is_active=True).update(is_active=False)
        project.is_active = True
        project.save()

        self.message_user(
            request,
            f"✅ Проект '{project.name}' активирован",
            level=messages.SUCCESS
        )


@admin.register(ArticleSource)
class ArticleSourceAdmin(admin.ModelAdmin):
    """Административная панель для RSS источников новостей."""

    list_display = (
        'name',
        'project',
        'is_active',
        'priority',
        'articles_count',
        'success_rate_display',
        'last_collected',
    )
    list_filter = ('is_active', 'project')
    search_fields = ('name', 'url')
    list_editable = ('is_active', 'priority')

    fieldsets = (
        ('Основная информация', {
            'fields': ('project', 'name', 'url'),
            'description': 'Настройки RSS ленты для сбора статей'
        }),
        ('Настройки', {
            'fields': ('is_active', 'priority')
        }),
        ('Статистика', {
            'classes': ('collapse',),
            'fields': ('last_collected', 'articles_count', 'success_rate')
        }),
    )

    def success_rate_display(self, obj):
        """Отображает процент успешности с цветом."""
        rate = obj.success_rate
        color = 'green' if rate > 50 else 'orange' if rate > 20 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, f'{rate:.1f}%')
    success_rate_display.short_description = 'Успешность'


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    """Административная панель для ключевых слов Google CSE."""

    list_display = ('keyword', 'project', 'priority', 'is_active', 'created_at')
    list_filter = ('is_active', 'priority', 'project')
    search_fields = ('keyword',)
    list_editable = ('priority', 'is_active')

    fieldsets = (
        ('Основная информация', {
            'fields': ('project', 'keyword'),
            'description': 'Ключевые слова используются для поиска через Google Custom Search Engine (CSE)'
        }),
        ('Настройки', {
            'fields': ('priority', 'is_active')
        }),
        ('Системная информация', {
            'classes': ('collapse',),
            'fields': ('created_at',)
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(DigestRun)
class DigestRunAdmin(admin.ModelAdmin):
    """Административная панель для запусков дайджеста."""

    list_display = (
        'id',
        'started_at',
        'status_badge',
        'duration_display',
        'total_articles_collected',
        'total_articles_filtered',
        'total_posts_created',
        'success_rate_display',
    )
    list_filter = ('status', 'started_at')
    search_fields = ('id',)
    readonly_fields = (
        'created_at',
        'started_at',
        'finished_at',
        'total_articles_collected',
        'total_articles_filtered',
        'total_posts_created',
        'total_images_generated',
        'duration_display',
        'success_rate_display',
        'filter_rate_display',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('status', 'created_at', 'started_at', 'finished_at')
        }),
        ('Статистика', {
            'fields': (
                'total_articles_collected',
                'total_articles_filtered',
                'total_posts_created',
                'total_images_generated',
                'duration_display',
                'success_rate_display',
                'filter_rate_display',
            )
        }),
        ('Ошибки', {
            'classes': ('collapse',),
            'fields': ('error_message',)
        }),
        ('Файлы', {
            'classes': ('collapse',),
            'fields': ('markdown_file', 'report_file')
        }),
    )

    inlines = [ArticleInline]

    def status_badge(self, obj):
        """Отображает статус с иконкой."""
        badges = {
            'running': '<span style="color: blue;">🔄 Выполняется</span>',
            'completed': '<span style="color: green;">✅ Завершен</span>',
            'failed': '<span style="color: red;">❌ Ошибка</span>',
            'partial': '<span style="color: orange;">⚠️ Частично</span>',
        }
        return format_html(badges.get(obj.status, obj.status))
    status_badge.short_description = 'Статус'

    def duration_display(self, obj):
        """Отображает продолжительность."""
        duration = obj.duration()
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        seconds = int(duration.total_seconds() % 60)

        if hours > 0:
            return f"{hours}ч {minutes}м {seconds}с"
        elif minutes > 0:
            return f"{minutes}м {seconds}с"
        else:
            return f"{seconds}с"
    duration_display.short_description = 'Продолжительность'

    def success_rate_display(self, obj):
        """Отображает процент успешности."""
        rate = obj.success_rate()
        color = 'green' if rate > 30 else 'orange' if rate > 10 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, f'{rate:.1f}%')
    success_rate_display.short_description = 'Успешность'

    def filter_rate_display(self, obj):
        """Отображает процент прохождения фильтра."""
        rate = obj.filter_rate()
        color = 'green' if rate > 40 else 'orange' if rate > 20 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, f'{rate:.1f}%')
    filter_rate_display.short_description = 'Прошло фильтр'

    def has_add_permission(self, request):
        """Запрещаем ручное создание запусков."""
        return False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Административная панель для статей."""

    list_display = (
        'short_title',
        'digest_run',
        'source',
        'content_type',
        'interest_score_badge',
        'is_relevant',
        'collected_at',
    )
    list_filter = (
        'is_relevant',
        'content_type',
        'digest_run',
        'source',
        'collected_at',
    )
    search_fields = ('title', 'summary', 'url')
    readonly_fields = (
        'digest_run',
        'source',
        'title',
        'url',
        'summary',
        'content_type',
        'interest_score',
        'is_relevant',
        'relevance_reason',
        'interest_reason',
        'collected_at',
        'url_link',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('digest_run', 'source', 'title', 'url_link', 'content_type')
        }),
        ('Контент', {
            'fields': ('summary',)
        }),
        ('Оценка', {
            'fields': (
                'interest_score',
                'is_relevant',
                'relevance_reason',
                'interest_reason',
            )
        }),
        ('Системная информация', {
            'classes': ('collapse',),
            'fields': ('collected_at',)
        }),
    )

    def short_title(self, obj):
        """Укороченный заголовок."""
        return obj.short_title
    short_title.short_description = 'Заголовок'

    def interest_score_badge(self, obj):
        """Отображает оценку интереса с цветом."""
        score = obj.interest_score
        color = 'green' if score >= 7 else 'orange' if score >= 5 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, f'{score:.1f}/10')
    interest_score_badge.short_description = 'Оценка'

    def url_link(self, obj):
        """Кликабельная ссылка."""
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url)
    url_link.short_description = 'Ссылка'

    def has_add_permission(self, request):
        """Запрещаем ручное создание статей."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление статей."""
        return False


@admin.register(GeneratedPost)
class GeneratedPostAdmin(admin.ModelAdmin):
    """Административная панель для сгенерированных постов."""

    list_display = (
        'article_title',
        'platform',
        'has_image_badge',
        'is_published',
        'generated_at',
        'published_at',
    )
    list_filter = ('platform', 'is_published', 'generated_at')
    search_fields = ('article__title', 'post_content')
    readonly_fields = (
        'article',
        'platform',
        'post_content',
        'image_idea',
        'image_path',
        'generated_at',
        'image_preview',
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('article', 'platform', 'generated_at')
        }),
        ('Контент', {
            'fields': ('post_content',)
        }),
        ('Изображение', {
            'fields': ('image_idea', 'image_path', 'image_preview')
        }),
        ('Публикация', {
            'fields': ('is_published', 'published_at')
        }),
    )

    def article_title(self, obj):
        """Заголовок статьи."""
        return obj.article.short_title
    article_title.short_description = 'Статья'

    def has_image_badge(self, obj):
        """Значок наличия изображения."""
        if obj.has_image:
            return format_html('<span style="color: green;">✅ Да</span>')
        return format_html('<span style="color: gray;">❌ Нет</span>')
    has_image_badge.short_description = 'Изображение'

    def image_preview(self, obj):
        """Превью изображения."""
        if obj.image_path:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px;" />',
                obj.image_path.url
            )
        return "Нет изображения"
    image_preview.short_description = 'Превью'

    def has_add_permission(self, request):
        """Запрещаем ручное создание постов."""
        return False
