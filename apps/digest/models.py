from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from typing import List

from . import prompts


class DigestRun(models.Model):
    """
    Модель для хранения информации о запуске пайплайна.
    """

    STATUS_CHOICES = [
        ("running", "Запущен"),
        ("completed", "Завершен"),
        ("failed", "Ошибка"),
        ("partial", "Частично завершен"),
    ]

    created_at = models.DateTimeField(
        "Дата создания",
        default=timezone.now,
    )
    started_at = models.DateTimeField(
        "Дата запуска",
        auto_now_add=True,
    )
    finished_at = models.DateTimeField(
        "Дата завершения",
        null=True,
        blank=True,
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default="running",
    )
    total_articles_collected = models.IntegerField(
        "Всего собрано статей",
        default=0,
    )
    total_articles_filtered = models.IntegerField(
        "Статей прошло фильтр",
        default=0,
    )
    total_posts_created = models.IntegerField(
        "Создано постов",
        default=0,
    )
    total_images_generated = models.IntegerField(
        "Сгенерировано изображений",
        default=0,
    )
    error_message = models.TextField(
        "Сообщение об ошибке",
        blank=True,
        null=True,
    )
    markdown_file = models.FileField(
        "Markdown файл с результатами",
        upload_to="digest/results/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    report_file = models.FileField(
        "Подробный отчет",
        upload_to="digest/reports/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Запуск дайджеста"
        verbose_name_plural = "Запуски дайджестов"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Digest от {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"

    def duration(self):
        """Возвращает продолжительность выполнения."""
        if self.finished_at:
            return self.finished_at - self.started_at
        return timezone.now() - self.started_at

    def success_rate(self):
        """Возвращает процент успешности (посты / собранные статьи)."""
        if self.total_articles_collected > 0:
            return (self.total_posts_created / self.total_articles_collected) * 100
        return 0

    def filter_rate(self):
        """Возвращает процент статей, прошедших фильтр."""
        if self.total_articles_collected > 0:
            return (self.total_articles_filtered / self.total_articles_collected) * 100
        return 0

    @property
    def is_running(self):
        """Проверяет, выполняется ли пайплайн в данный момент."""
        return self.status == "running"

    @property
    def is_completed(self):
        """Проверяет, успешно ли завершен пайплайн."""
        return self.status == "completed"

    @property
    def is_failed(self):
        """Проверяет, завершился ли пайплайн с ошибкой."""
        return self.status == "failed"


class ArticleSource(models.Model):
    """
    Модель для хранения RSS источников новостей.
    Каждый источник представляет собой RSS ленту для сбора статей.
    """

    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='sources',
        verbose_name='Проект',
        null=True,  # Временно для миграции
        blank=True,
    )
    name = models.CharField(
        "Название RSS источника",
        max_length=200,
        help_text="Название RSS ленты (например, 'Python.org Blog')",
    )
    url = models.URLField(
        "URL RSS ленты",
        max_length=500,
        blank=True,
        null=True,
        help_text=(
            "Полный URL RSS/Atom фида (не обычная веб-страница!).\n"
            "Примеры:\n"
            "• https://www.python.org/feeds/python.rss/\n"
            "• https://habr.com/ru/rss/all/\n"
            "• https://realpython.com/atom.xml"
        ),
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )
    priority = models.IntegerField(
        "Приоритет",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1 - самый высокий приоритет",
    )
    last_collected = models.DateTimeField(
        "Последний сбор",
        blank=True,
        null=True,
    )
    articles_count = models.IntegerField(
        "Всего собрано статей",
        default=0,
    )
    success_rate = models.FloatField(
        "Процент успешных публикаций",
        default=0,
        help_text="Процент статей из этого источника, которые были опубликованы",
    )

    class Meta:
        verbose_name = "RSS источник"
        verbose_name_plural = "RSS источники"
        ordering = ["priority", "name"]
        indexes = [
            models.Index(fields=["project", "is_active", "priority"]),
        ]

    def __str__(self):
        project_name = self.project.name if self.project else "Без проекта"
        return f"{self.name} - {project_name}"


class Article(models.Model):
    """
    Модель для хранения собранных статей.
    """

    CONTENT_TYPE_CHOICES = [
        ("tutorial", "Туториал"),
        ("news", "Новость"),
        ("library", "Библиотека/Инструмент"),
        ("event", "Событие"),
        ("opinion", "Мнение"),
        ("meme", "Мем/Юмор"),
        ("other", "Другое"),
    ]

    digest_run = models.ForeignKey(
        DigestRun,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="Запуск дайджеста",
    )
    source = models.ForeignKey(
        ArticleSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Источник",
    )
    title = models.CharField(
        "Заголовок",
        max_length=500,
    )
    url = models.URLField(
        "URL статьи",
        max_length=1000,
    )
    summary = models.TextField(
        "Краткое содержание",
        blank=True,
        null=True,
    )
    content_type = models.CharField(
        "Тип контента",
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="other",
    )
    interest_score = models.FloatField(
        "Оценка интереса",
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0,
    )
    is_relevant = models.BooleanField(
        "Релевантен",
        default=False,
    )
    relevance_reason = models.TextField(
        "Причина релевантности",
        blank=True,
        null=True,
    )
    interest_reason = models.TextField(
        "Причина интереса",
        blank=True,
        null=True,
    )
    collected_at = models.DateTimeField(
        "Дата сбора",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ["-interest_score", "-collected_at"]
        indexes = [
            models.Index(fields=["digest_run", "is_relevant"]),
            models.Index(fields=["interest_score"]),
            models.Index(fields=["collected_at"]),
            models.Index(fields=["source", "collected_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["digest_run", "url"],
                name="unique_article_per_digest"
            ),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.interest_score}/10)"

    @property
    def is_high_quality(self):
        """Определяет, является ли статья высококачественной (оценка >= 7)."""
        return self.interest_score >= 7.0

    @property
    def short_title(self):
        """Возвращает укороченный заголовок для отображения."""
        return self.title[:100] if len(self.title) > 100 else self.title


class GeneratedPost(models.Model):
    """
    Модель для хранения сгенерированных постов.
    """

    PLATFORM_CHOICES = [
        ("telegram", "Telegram"),
        ("twitter", "Twitter/X"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
        ("general", "Общий"),
    ]

    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name="generated_post",
        verbose_name="Статья",
    )
    platform = models.CharField(
        "Платформа",
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="general",
    )
    post_content = models.TextField(
        "Текст поста",
    )
    image_idea = models.TextField(
        "Идея для изображения",
        blank=True,
        null=True,
    )
    image_path = models.ImageField(
        "Изображение",
        upload_to="digest/images/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    generated_at = models.DateTimeField(
        "Дата генерации",
        auto_now_add=True,
    )
    is_published = models.BooleanField(
        "Опубликован",
        default=False,
    )
    published_at = models.DateTimeField(
        "Дата публикации",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Сгенерированный пост"
        verbose_name_plural = "Сгенерированные посты"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["platform", "is_published"]),
            models.Index(fields=["generated_at"]),
        ]

    def __str__(self):
        return f"Пост для {self.article.title[:30]}... ({self.get_platform_display()})"

    @property
    def has_image(self):
        """Проверяет, есть ли у поста изображение."""
        return bool(self.image_path)

    @property
    def days_since_publication(self):
        """Возвращает количество дней с момента публикации."""
        if self.published_at:
            return (timezone.now() - self.published_at).days
        return None


class Project(models.Model):
    """
    Модель для хранения конфигурации пайплайна.
    """

    name = models.CharField(
        "Название конфигурации",
        max_length=100,
        unique=True,
    )
    filter_system_prompt = models.TextField(
        "System prompt для фильтра",
        default=prompts.FILTER_SYSTEM_PROMPT,
        help_text="Системный промпт для агента фильтрации статей",
    )
    filter_user_prompt = models.TextField(
        "User prompt для фильтра",
        default=prompts.FILTER_USER_PROMPT,
        help_text="Промпт для пользователя в агенте фильтрации. Доступные переменные: {title}, {summary}, {url}, {format_instructions}",
    )
    copywriter_system_prompt = models.TextField(
        "System prompt для копирайтера",
        default=prompts.COPYWRITER_SYSTEM_PROMPT,
        help_text="Системный промпт для агента создания постов",
    )
    copywriter_user_prompt = models.TextField(
        "User prompt для копирайтера",
        default=prompts.COPYWRITER_USER_PROMPT,
        help_text="Промпт для пользователя в агенте копирайтинга. Доступные переменные: {title}, {summary}, {url}, {format_instructions}",
    )
    rss_hours_period = models.IntegerField(
        "Период RSS (часы)",
        default=168,
        validators=[MinValueValidator(1), MaxValueValidator(720)],
        help_text="За какой период собирать RSS (по умолчанию 168 = 7 дней, максимум 30 дней)",
    )
    max_articles_per_source = models.IntegerField(
        "Максимум статей с источника",
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Лимит статей с одного источника за запуск",
    )
    max_final_posts = models.IntegerField(
        "Максимум финальных постов",
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Сколько ТОП статей выбирать для публикации",
    )
    enable_google_news = models.BooleanField(
        "Включить Google Custom Search",
        default=False,
        help_text="Поиск статей через Google CSE по ключевым словам (настраиваются ниже)",
    )
    enable_rss_news = models.BooleanField(
        "Включить RSS сбор",
        default=True,
        help_text="Сбор статей из RSS лент (источники настраиваются ниже)",
    )
    generate_images = models.BooleanField(
        "Генерировать изображения",
        default=False,
    )
    enable_email_sending = models.BooleanField(
        "Включить отправку email",
        default=False,
    )
    is_active = models.BooleanField(
        "Активная конфигурация",
        default=False,
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-is_active", "name"]
        db_table = "digest_configuration"  # Сохраняем старое имя таблицы

    def __str__(self):
        status = "✅ Активный" if self.is_active else "❌ Неактивный"
        return f"{self.name} ({status})"

    def save(self, *args, **kwargs):
        """
        Гарантирует, что только одна конфигурация активна.
        """
        if self.is_active:
            # Деактивируем все другие конфигурации
            Project.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        """
        Возвращает активный проект.

        Returns:
            Project: Активный проект или None
        """
        return cls.objects.filter(is_active=True).first()

    def get_rss_sources(self):
        """
        Возвращает активные RSS источники для этого проекта.

        Returns:
            QuerySet: Активные RSS источники
        """
        return self.sources.filter(is_active=True).order_by('priority')

    def get_active_keywords(self):
        """
        Возвращает активные ключевые слова для этого проекта.

        Returns:
            List[str]: Список активных ключевых слов
        """
        return list(
            self.keywords.filter(is_active=True)
            .order_by('priority')
            .values_list('keyword', flat=True)
        )


class Keyword(models.Model):
    """
    Модель для хранения ключевых слов для Google Custom Search Engine (CSE).
    Используются для поиска статей через Google Search API.
    """

    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='keywords',
        verbose_name='Проект',
        null=True,  # Временно для миграции
        blank=True,
    )
    keyword = models.CharField(
        "Ключевое слово (для Google CSE)",
        max_length=200,
        help_text="Ключевое слово для поиска через Google Custom Search",
    )
    is_active = models.BooleanField(
        "Активно",
        default=True,
    )
    priority = models.IntegerField(
        "Приоритет",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Ключевое слово (Google CSE)"
        verbose_name_plural = "Ключевые слова (Google CSE)"
        ordering = ["priority", "keyword"]
        unique_together = [['project', 'keyword']]  # Уникальность в рамках проекта
        indexes = [
            models.Index(fields=["project", "is_active", "priority"]),
        ]

    def __str__(self):
        project_name = self.project.name if self.project else "Без проекта"
        return f"{self.keyword} ({project_name})"
