"""
Модуль для интеграции сервисов с Django моделями.
Обеспечивает сохранение результатов обработки в базу данных.
"""

from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from ..models import (
    DigestRun,
    ArticleSource,
    Article,
    GeneratedPost,
    Project,
    Keyword,
)
from .scout_service import ScoutService
from .filter_service import FilterService
from .copywriter_service import CopywriterService


class IntegrationService:
    """
    Сервис для интеграции между бизнес-логикой и базой данных.
    Обеспечивает сохранение результатов работы пайплайна в модели Django.
    """

    def __init__(self):
        self.scout_service = ScoutService()
        self.filter_service = FilterService()
        self.copywriter_service = CopywriterService()

    def create_digest_run(self) -> DigestRun:
        """
        Создает новую запись о запуске пайплайна.

        Returns:
            DigestRun: Созданный объект запуска
        """
        digest_run = DigestRun.objects.create(
            status="running", started_at=datetime.now()
        )
        logger.info(f"Создан новый запуск дайджеста: {digest_run.id}")
        return digest_run

    def update_digest_run_stats(
        self,
        digest_run: DigestRun,
        total_collected: int = 0,
        total_filtered: int = 0,
        total_posts: int = 0,
        total_images: int = 0,
        status: str = "running",
        error_message: Optional[str] = None,
    ) -> None:
        """
        Обновляет статистику запуска дайджеста.

        Args:
            digest_run: Объект запуска дайджеста
            total_collected: Всего собрано статей
            total_filtered: Статей прошло фильтр
            total_posts: Создано постов
            total_images: Сгенерировано изображений
            status: Статус выполнения
            error_message: Сообщение об ошибке (если есть)
        """
        digest_run.total_articles_collected = total_collected
        digest_run.total_articles_filtered = total_filtered
        digest_run.total_posts_created = total_posts
        digest_run.total_images_generated = total_images
        digest_run.status = status
        digest_run.error_message = error_message
        if status in ["completed", "failed", "partial"]:
            digest_run.finished_at = datetime.now()
        digest_run.save()

        logger.info(f"Обновлена статистика запуска {digest_run.id}: {status}")

    def get_or_create_news_source(
        self, source_name: str, source_url: str
    ) -> ArticleSource:
        """
        Получает или создает RSS источник новостей.

        Args:
            source_name: Название источника
            source_url: URL источника

        Returns:
            ArticleSource: Объект источника новостей
        """
        source, created = ArticleSource.objects.get_or_create(
            name=source_name,
            defaults={"url": source_url, "is_active": True},
        )

        if created:
            logger.info(f"Создан новый RSS источник: {source_name}")
        else:
            logger.debug(f"Используется существующий источник: {source_name}")

        return source

    def save_articles_to_db(
        self,
        digest_run: DigestRun,
        articles: List[Dict[str, str]],
        source: Optional[ArticleSource] = None,
    ) -> List[Article]:
        """
        Сохраняет собранные статьи в базу данных.

        Args:
            digest_run: Объект запуска дайджеста
            articles: Список статей для сохранения
            source: Источник новостей (опционально)

        Returns:
            List[Article]: Список созданных объектов статей
        """
        saved_articles = []

        for article_data in articles:
            try:
                # Определяем источник из данных статьи, если не передан
                article_source = source
                if not article_source and "source" in article_data:
                    source_info = article_data["source"]
                    if "Google Search" in source_info:
                        article_source = self.get_or_create_news_source(
                            f"Google Search: {source_info.split(':')[-1].strip()}",
                            "",
                        )
                    elif "RSS" in source_info:
                        article_source = self.get_or_create_news_source(
                            source_info, ""
                        )

                # Создаем статью
                article = Article.objects.create(
                    digest_run=digest_run,
                    source=article_source,
                    title=article_data.get("title", ""),
                    url=article_data.get("url", ""),
                    summary=article_data.get("summary", ""),
                    content_type=article_data.get("content_type", "other"),
                    interest_score=article_data.get("interest_score", 0),
                    is_relevant=article_data.get("is_relevant", False),
                    relevance_reason=article_data.get("relevance_reason", ""),
                    interest_reason=article_data.get("interest_reason", ""),
                )

                saved_articles.append(article)

            except Exception as e:
                logger.error(
                    f"Ошибка сохранения статьи '{article_data.get('title', '')}': {e}"
                )
                continue

        logger.info(f"Сохранено {len(saved_articles)} статей в базу данных")
        return saved_articles

    def save_generated_posts(
        self, articles_with_posts: List[Dict[str, str]]
    ) -> List[GeneratedPost]:
        """
        Сохраняет сгенерированные посты в базу данных.

        Args:
            articles_with_posts: Список статей с постами

        Returns:
            List[GeneratedPost]: Список созданных объектов постов
        """
        saved_posts = []

        for article_data in articles_with_posts:
            try:
                # Находим соответствующую статью в базе
                article = Article.objects.filter(
                    url=article_data.get("url", "")
                ).first()

                if not article:
                    logger.warning(
                        f"Статья для поста не найдена: {article_data.get('title', '')}"
                    )
                    continue

                # Создаем пост
                post = GeneratedPost.objects.create(
                    article=article,
                    platform="telegram",  # По умолчанию Telegram
                    post_content=article_data.get("post_content", ""),
                    image_idea=article_data.get("image_idea", ""),
                    image_path=article_data.get("image_path", ""),
                    is_published=False,
                )

                saved_posts.append(post)

            except Exception as e:
                logger.error(
                    f"Ошибка сохранения поста для статьи '{article_data.get('title', '')}': {e}"
                )
                continue

        logger.info(f"Сохранено {len(saved_posts)} постов в базу данных")
        return saved_posts

    def get_active_configuration(self) -> Optional[Project]:
        """
        Получает активную конфигурацию пайплайна.

        Returns:
            Project: Активная конфигурация или None
        """
        try:
            config = Project.objects.get(is_active=True)
            logger.info(f"Используется конфигурация: {config.name}")
            return config
        except Project.DoesNotExist:
            logger.warning("Активная конфигурация не найдена")
            return None
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации: {e}")
            return None

    def get_active_keywords(self) -> List[str]:
        """
        Получает список активных ключевых слов.

        Returns:
            List[str]: Список активных ключевых слов
        """
        keywords = list(
            Keyword.objects.filter(is_active=True).values_list("keyword", flat=True)
        )
        logger.info(f"Получено {len(keywords)} активных ключевых слов")
        return keywords
