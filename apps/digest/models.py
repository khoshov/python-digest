"""
Модели для приложения digest.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class DigestRun(models.Model):
    """
    Модель для хранения информации о запуске пайплайна.
    """
    
    STATUS_CHOICES = [
        ('running', 'Запущен'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
        ('partial', 'Частично завершен'),
    ]
    
    created_at = models.DateTimeField(
        'Дата создания',
        default=timezone.now
    )
    started_at = models.DateTimeField(
        'Дата запуска',
        auto_now_add=True
    )
    finished_at = models.DateTimeField(
        'Дата завершения',
        null=True,
        blank=True
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='running'
    )
    total_articles_collected = models.IntegerField(
        'Всего собрано статей',
        default=0
    )
    total_articles_filtered = models.IntegerField(
        'Статей прошло фильтр',
        default=0
    )
    total_posts_created = models.IntegerField(
        'Создано постов',
        default=0
    )
    total_images_generated = models.IntegerField(
        'Сгенерировано изображений',
        default=0
    )
    error_message = models.TextField(
        'Сообщение об ошибке',
        blank=True,
        null=True
    )
    markdown_file = models.FileField(
        'Markdown файл с результатами',
        upload_to='digest/results/%Y/%m/%d/',
        blank=True,
        null=True
    )
    report_file = models.FileField(
        'Подробный отчет',
        upload_to='digest/reports/%Y/%m/%d/',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Запуск дайджеста'
        verbose_name_plural = 'Запуски дайджестов'
        ordering = ['-started_at']
    
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


class NewsSource(models.Model):
    """
    Модель для хранения источников новостей.
    """
    
    SOURCE_TYPE_CHOICES = [
        ('rss', 'RSS лента'),
        ('google', 'Google Search'),
        ('manual', 'Ручной ввод'),
    ]
    
    name = models.CharField(
        'Название источника',
        max_length=200
    )
    url = models.URLField(
        'URL источника',
        max_length=500,
        blank=True,
        null=True
    )
    source_type = models.CharField(
        'Тип источника',
        max_length=20,
        choices=SOURCE_TYPE_CHOICES
    )
    is_active = models.BooleanField(
        'Активен',
        default=True
    )
    priority = models.IntegerField(
        'Приоритет',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='1 - самый высокий приоритет'
    )
    last_collected = models.DateTimeField(
        'Последний сбор',
        blank=True,
        null=True
    )
    articles_count = models.IntegerField(
        'Всего собрано статей',
        default=0
    )
    success_rate = models.FloatField(
        'Процент успешных публикаций',
        default=0,
        help_text='Процент статей из этого источника, которые были опубликованы'
    )
    
    class Meta:
        verbose_name = 'Источник новостей'
        verbose_name_plural = 'Источники новостей'
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class Article(models.Model):
    """
    Модель для хранения собранных статей.
    """
    
    CONTENT_TYPE_CHOICES = [
        ('tutorial', 'Туториал'),
        ('news', 'Новость'),
        ('library', 'Библиотека/Инструмент'),
        ('event', 'Событие'),
        ('opinion', 'Мнение'),
        ('meme', 'Мем/Юмор'),
        ('other', 'Другое'),
    ]
    
    digest_run = models.ForeignKey(
        DigestRun,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Запуск дайджеста'
    )
    source = models.ForeignKey(
        NewsSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Источник'
    )
    title = models.CharField(
        'Заголовок',
        max_length=500
    )
    url = models.URLField(
        'URL статьи',
        max_length=1000
    )
    summary = models.TextField(
        'Краткое содержание',
        blank=True,
        null=True
    )
    content_type = models.CharField(
        'Тип контента',
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='other'
    )
    interest_score = models.FloatField(
        'Оценка интереса',
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0
    )
    is_relevant = models.BooleanField(
        'Релевантен',
        default=False
    )
    relevance_reason = models.TextField(
        'Причина релевантности',
        blank=True,
        null=True
    )
    interest_reason = models.TextField(
        'Причина интереса',
        blank=True,
        null=True
    )
    collected_at = models.DateTimeField(
        'Дата сбора',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-interest_score', '-collected_at']
        indexes = [
            models.Index(fields=['digest_run', 'is_relevant']),
            models.Index(fields=['interest_score']),
            models.Index(fields=['collected_at']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.interest_score}/10)"


class GeneratedPost(models.Model):
    """
    Модель для хранения сгенерированных постов.
    """
    
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('general', 'Общий'),
    ]
    
    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name='generated_post',
        verbose_name='Статья'
    )
    platform = models.CharField(
        'Платформа',
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='general'
    )
    post_content = models.TextField(
        'Текст поста'
    )
    image_idea = models.TextField(
        'Идея для изображения',
        blank=True,
        null=True
    )
    image_path = models.ImageField(
        'Изображение',
        upload_to='digest/images/%Y/%m/%d/',
        blank=True,
        null=True
    )
    generated_at = models.DateTimeField(
        'Дата генерации',
        auto_now_add=True
    )
    is_published = models.BooleanField(
        'Опубликован',
        default=False
    )
    published_at = models.DateTimeField(
        'Дата публикации',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'Сгенерированный пост'
        verbose_name_plural = 'Сгенерированные посты'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['platform', 'is_published']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return f"Пост для {self.article.title[:30]}... ({self.get_platform_display()})"


class Configuration(models.Model):
    """
    Модель для хранения конфигурации пайплайна.
    """
    
    name = models.CharField(
        'Название конфигурации',
        max_length=100,
        unique=True
    )
    flowise_host = models.URLField(
        'Flowise Host',
        max_length=500
    )
    flowise_filter_id = models.CharField(
        'Flowise Filter ID',
        max_length=100
    )
    flowise_copywriter_id = models.CharField(
        'Flowise Copywriter ID',
        max_length=100
    )
    google_api_key = models.CharField(
        'Google API Key',
        max_length=200,
        blank=True,
        null=True
    )
    google_cse_id = models.CharField(
        'Google CSE ID',
        max_length=100,
        blank=True,
        null=True
    )
    openai_api_key = models.CharField(
        'OpenAI API Key',
        max_length=200,
        blank=True,
        null=True
    )
    rss_hours_period = models.IntegerField(
        'Период RSS (часы)',
        default=168,
        help_text='За какой период собирать RSS (по умолчанию 168 = 7 дней)'
    )
    max_articles_per_source = models.IntegerField(
        'Максимум статей с источника',
        default=20
    )
    max_final_posts = models.IntegerField(
        'Максимум финальных постов',
        default=8,
        help_text='Сколько ТОП статей выбирать для публикации'
    )
    enable_google_news = models.BooleanField(
        'Включить Google News',
        default=False
    )
    enable_rss_news = models.BooleanField(
        'Включить RSS',
        default=True
    )
    generate_images = models.BooleanField(
        'Генерировать изображения',
        default=False
    )
    enable_email_sending = models.BooleanField(
        'Включить отправку email',
        default=False
    )
    email_recipients = models.TextField(
        'Получатели email',
        blank=True,
        null=True,
        help_text='Email адреса через запятую'
    )
    is_active = models.BooleanField(
        'Активная конфигурация',
        default=False
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Конфигурация'
        verbose_name_plural = 'Конфигурации'
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        status = "✅ Активная" if self.is_active else "❌ Неактивная"
        return f"{self.name} ({status})"
    
    def save(self, *args, **kwargs):
        """
        Гарантирует, что только одна конфигурация активна.
        """
        if self.is_active:
            # Деактивируем все другие конфигурации
            Configuration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class Keyword(models.Model):
    """
    Модель для хранения ключевых слов для поиска.
    """
    
    keyword = models.CharField(
        'Ключевое слово',
        max_length=200,
        unique=True
    )
    is_active = models.BooleanField(
        'Активно',
        default=True
    )
    priority = models.IntegerField(
        'Приоритет',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Ключевое слово'
        verbose_name_plural = 'Ключевые слова'
        ordering = ['priority', 'keyword']
    
    def __str__(self):
        return self.keyword
