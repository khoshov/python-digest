"""
Тесты для моделей приложения digest.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from apps.digest.models import (
    DigestRun,
    ArticleSource,
    Article,
    GeneratedPost,
    Project,
    Keyword,
)


class ProjectModelTest(TestCase):
    """Тесты для модели Project."""

    def setUp(self):
        """Создание тестовых данных."""
        self.project = Project.objects.create(
            name="Test Project",
            is_active=True,
            rss_hours_period=168,
            max_articles_per_source=20,
            max_final_posts=8,
        )

    def test_project_creation(self):
        """Тест создания проекта."""
        self.assertEqual(self.project.name, "Test Project")
        self.assertTrue(self.project.is_active)
        self.assertEqual(self.project.rss_hours_period, 168)

    def test_only_one_active_project(self):
        """Тест, что только один проект может быть активным."""
        project2 = Project.objects.create(
            name="Test Project 2",
            is_active=True,
        )

        # Первый проект должен стать неактивным
        self.project.refresh_from_db()
        self.assertFalse(self.project.is_active)
        self.assertTrue(project2.is_active)

    def test_get_active_project(self):
        """Тест получения активного проекта."""
        active_project = Project.get_active()
        self.assertEqual(active_project, self.project)

    def test_get_active_when_no_active(self):
        """Тест получения активного проекта, когда нет активных."""
        self.project.is_active = False
        self.project.save()

        active_project = Project.get_active()
        self.assertIsNone(active_project)

    def test_rss_hours_period_validation(self):
        """Тест валидации периода RSS."""
        project = Project(
            name="Invalid Project",
            rss_hours_period=1000,  # Больше максимума (720)
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_max_articles_validation(self):
        """Тест валидации максимума статей."""
        project = Project(
            name="Invalid Project",
            max_articles_per_source=200,  # Больше максимума (100)
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_get_rss_sources(self):
        """Тест получения RSS источников."""
        source1 = ArticleSource.objects.create(
            project=self.project,
            name="RSS Source 1",
            url="https://example.com/rss",
            is_active=True,
            priority=1,
        )
        source2 = ArticleSource.objects.create(
            project=self.project,
            name="RSS Source 2",
            url="https://example.com/rss2",
            is_active=False,
            priority=2,
        )

        rss_sources = self.project.get_rss_sources()
        self.assertEqual(rss_sources.count(), 1)
        self.assertEqual(rss_sources.first(), source1)

    def test_get_active_keywords(self):
        """Тест получения активных ключевых слов."""
        Keyword.objects.create(
            project=self.project,
            keyword="Python",
            is_active=True,
            priority=1,
        )
        Keyword.objects.create(
            project=self.project,
            keyword="Django",
            is_active=False,
            priority=2,
        )

        keywords = self.project.get_active_keywords()
        self.assertEqual(len(keywords), 1)
        self.assertEqual(keywords[0], "Python")


class KeywordModelTest(TestCase):
    """Тесты для модели Keyword."""

    def setUp(self):
        """Создание тестовых данных."""
        self.project = Project.objects.create(name="Test Project")

    def test_keyword_creation(self):
        """Тест создания ключевого слова."""
        keyword = Keyword.objects.create(
            project=self.project,
            keyword="Python",
            priority=1,
        )
        self.assertEqual(keyword.keyword, "Python")
        self.assertEqual(keyword.project, self.project)

    def test_unique_keyword_per_project(self):
        """Тест уникальности ключевого слова в рамках проекта."""
        Keyword.objects.create(
            project=self.project,
            keyword="Python",
        )

        # Попытка создать дубликат в том же проекте
        with self.assertRaises(Exception):
            Keyword.objects.create(
                project=self.project,
                keyword="Python",
            )

    def test_same_keyword_different_projects(self):
        """Тест, что одно ключевое слово может быть в разных проектах."""
        project2 = Project.objects.create(name="Test Project 2")

        keyword1 = Keyword.objects.create(
            project=self.project,
            keyword="Python",
        )
        keyword2 = Keyword.objects.create(
            project=project2,
            keyword="Python",
        )

        self.assertNotEqual(keyword1.id, keyword2.id)

    def test_priority_validation(self):
        """Тест валидации приоритета."""
        keyword = Keyword(
            project=self.project,
            keyword="Python",
            priority=10,  # Больше максимума (5)
        )
        with self.assertRaises(ValidationError):
            keyword.full_clean()


class ArticleSourceModelTest(TestCase):
    """Тесты для модели ArticleSource."""

    def setUp(self):
        """Создание тестовых данных."""
        self.project = Project.objects.create(name="Test Project")

    def test_article_source_creation(self):
        """Тест создания источника."""
        source = ArticleSource.objects.create(
            project=self.project,
            name="Test Source",
            url="https://example.com/rss",
            priority=1,
        )
        self.assertEqual(source.name, "Test Source")
        self.assertEqual(source.project, self.project)

    def test_priority_validation(self):
        """Тест валидации приоритета."""
        source = ArticleSource(
            project=self.project,
            name="Test Source",
            priority=15,  # Больше максимума (10)
        )
        with self.assertRaises(ValidationError):
            source.full_clean()


class DigestRunModelTest(TestCase):
    """Тесты для модели DigestRun."""

    def setUp(self):
        """Создание тестовых данных."""
        self.digest_run = DigestRun.objects.create(
            status="running",
            total_articles_collected=100,
            total_articles_filtered=50,
            total_posts_created=10,
        )

    def test_digest_run_creation(self):
        """Тест создания запуска дайджеста."""
        self.assertEqual(self.digest_run.status, "running")
        self.assertEqual(self.digest_run.total_articles_collected, 100)

    def test_duration(self):
        """Тест вычисления продолжительности."""
        duration = self.digest_run.duration()
        self.assertIsNotNone(duration)
        self.assertIsInstance(duration, timedelta)

    def test_duration_with_finished(self):
        """Тест продолжительности для завершенного запуска."""
        self.digest_run.finished_at = timezone.now() + timedelta(hours=1)
        self.digest_run.save()

        duration = self.digest_run.duration()
        self.assertGreater(duration.total_seconds(), 3600)  # Больше часа

    def test_success_rate(self):
        """Тест вычисления процента успешности."""
        rate = self.digest_run.success_rate()
        self.assertEqual(rate, 10.0)  # 10 постов из 100 статей

    def test_success_rate_zero_articles(self):
        """Тест процента успешности при нуле статей."""
        digest_run = DigestRun.objects.create(
            status="running",
            total_articles_collected=0,
        )
        rate = digest_run.success_rate()
        self.assertEqual(rate, 0)

    def test_filter_rate(self):
        """Тест вычисления процента фильтрации."""
        rate = self.digest_run.filter_rate()
        self.assertEqual(rate, 50.0)  # 50 из 100

    def test_is_running_property(self):
        """Тест свойства is_running."""
        self.assertTrue(self.digest_run.is_running)
        self.assertFalse(self.digest_run.is_completed)
        self.assertFalse(self.digest_run.is_failed)

    def test_is_completed_property(self):
        """Тест свойства is_completed."""
        self.digest_run.status = "completed"
        self.digest_run.save()

        self.assertFalse(self.digest_run.is_running)
        self.assertTrue(self.digest_run.is_completed)
        self.assertFalse(self.digest_run.is_failed)

    def test_is_failed_property(self):
        """Тест свойства is_failed."""
        self.digest_run.status = "failed"
        self.digest_run.save()

        self.assertFalse(self.digest_run.is_running)
        self.assertFalse(self.digest_run.is_completed)
        self.assertTrue(self.digest_run.is_failed)


class ArticleModelTest(TestCase):
    """Тесты для модели Article."""

    def setUp(self):
        """Создание тестовых данных."""
        self.digest_run = DigestRun.objects.create(status="running")
        self.project = Project.objects.create(name="Test Project")
        self.source = ArticleSource.objects.create(
            project=self.project,
            name="Test Source",
        )

    def test_article_creation(self):
        """Тест создания статьи."""
        article = Article.objects.create(
            digest_run=self.digest_run,
            source=self.source,
            title="Test Article",
            url="https://example.com/article",
            summary="Test summary",
            content_type="news",
            interest_score=8.5,
            is_relevant=True,
        )
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.interest_score, 8.5)

    def test_is_high_quality_property(self):
        """Тест свойства is_high_quality."""
        article = Article.objects.create(
            digest_run=self.digest_run,
            title="High Quality Article",
            url="https://example.com/article1",
            interest_score=8.0,
        )
        self.assertTrue(article.is_high_quality)

        low_article = Article.objects.create(
            digest_run=self.digest_run,
            title="Low Quality Article",
            url="https://example.com/article2",
            interest_score=5.0,
        )
        self.assertFalse(low_article.is_high_quality)

    def test_short_title_property(self):
        """Тест свойства short_title."""
        short_article = Article.objects.create(
            digest_run=self.digest_run,
            title="Short",
            url="https://example.com/article1",
        )
        self.assertEqual(short_article.short_title, "Short")

        long_article = Article.objects.create(
            digest_run=self.digest_run,
            title="A" * 150,
            url="https://example.com/article2",
        )
        self.assertEqual(len(long_article.short_title), 100)

    def test_unique_url_per_digest(self):
        """Тест уникальности URL в рамках одного дайджеста."""
        Article.objects.create(
            digest_run=self.digest_run,
            title="Article 1",
            url="https://example.com/article",
        )

        # Попытка создать дубликат в том же дайджесте
        with self.assertRaises(Exception):
            Article.objects.create(
                digest_run=self.digest_run,
                title="Article 2",
                url="https://example.com/article",
            )

    def test_same_url_different_digests(self):
        """Тест, что один URL может быть в разных дайджестах."""
        digest_run2 = DigestRun.objects.create(status="running")

        article1 = Article.objects.create(
            digest_run=self.digest_run,
            title="Article 1",
            url="https://example.com/article",
        )
        article2 = Article.objects.create(
            digest_run=digest_run2,
            title="Article 2",
            url="https://example.com/article",
        )

        self.assertNotEqual(article1.id, article2.id)

    def test_interest_score_validation(self):
        """Тест валидации оценки интереса."""
        article = Article(
            digest_run=self.digest_run,
            title="Test",
            url="https://example.com/article",
            interest_score=15,  # Больше максимума (10)
        )
        with self.assertRaises(ValidationError):
            article.full_clean()


class GeneratedPostModelTest(TestCase):
    """Тесты для модели GeneratedPost."""

    def setUp(self):
        """Создание тестовых данных."""
        self.digest_run = DigestRun.objects.create(status="running")
        self.article = Article.objects.create(
            digest_run=self.digest_run,
            title="Test Article",
            url="https://example.com/article",
        )

    def test_generated_post_creation(self):
        """Тест создания сгенерированного поста."""
        post = GeneratedPost.objects.create(
            article=self.article,
            platform="telegram",
            post_content="Test content",
        )
        self.assertEqual(post.platform, "telegram")
        self.assertEqual(post.article, self.article)

    def test_has_image_property(self):
        """Тест свойства has_image."""
        post = GeneratedPost.objects.create(
            article=self.article,
            platform="telegram",
            post_content="Test",
        )
        self.assertFalse(post.has_image)

    def test_days_since_publication(self):
        """Тест свойства days_since_publication."""
        post = GeneratedPost.objects.create(
            article=self.article,
            platform="telegram",
            post_content="Test",
        )
        self.assertIsNone(post.days_since_publication)

        post.is_published = True
        post.published_at = timezone.now() - timedelta(days=5)
        post.save()

        self.assertEqual(post.days_since_publication, 5)
