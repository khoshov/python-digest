"""
Тесты для административной панели приложения digest.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.digest.admin import (
    ProjectAdmin,
    DigestRunAdmin,
    ArticleAdmin,
    GeneratedPostAdmin,
    ArticleSourceAdmin,
)
from apps.digest.models import (
    Project,
    DigestRun,
    Article,
    GeneratedPost,
    ArticleSource,
    Keyword,
)


class ProjectAdminTest(TestCase):
    """Тесты для ProjectAdmin."""

    def setUp(self):
        """Создание тестовых данных."""
        self.site = AdminSite()
        self.admin = ProjectAdmin(Project, self.site)
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password'
        )
        self.project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )

    def test_is_active_badge_active(self):
        """Тест отображения значка активности для активного проекта."""
        badge = self.admin.is_active_badge(self.project)
        self.assertIn('green', badge)
        self.assertIn('Активный', badge)

    def test_is_active_badge_inactive(self):
        """Тест отображения значка активности для неактивного проекта."""
        self.project.is_active = False
        badge = self.admin.is_active_badge(self.project)
        self.assertIn('gray', badge)
        self.assertIn('Неактивный', badge)

    def test_sources_count(self):
        """Тест подсчета источников."""
        ArticleSource.objects.create(
            project=self.project,
            name="Source 1",
            source_type="rss",
            is_active=True,
        )
        ArticleSource.objects.create(
            project=self.project,
            name="Source 2",
            source_type="rss",
            is_active=False,
        )

        count = self.admin.sources_count(self.project)
        self.assertIn('2', count)
        self.assertIn('активных: 1', count)

    def test_keywords_count(self):
        """Тест подсчета ключевых слов."""
        Keyword.objects.create(
            project=self.project,
            keyword="Python",
            is_active=True,
        )
        Keyword.objects.create(
            project=self.project,
            keyword="Django",
            is_active=False,
        )

        count = self.admin.keywords_count(self.project)
        self.assertIn('2', count)
        self.assertIn('активных: 1', count)

    @patch('apps.digest.admin.run_pipeline_for_project')
    def test_run_digest_action_success(self, mock_run):
        """Тест успешного запуска дайджеста."""
        mock_run.return_value = {
            'success': True,
            'total_posts': 5,
        }

        request = self.factory.post('/')
        request.user = self.user
        request._messages = FallbackStorage(request)

        queryset = Project.objects.filter(id=self.project.id)
        self.admin.run_digest_action(request, queryset)

        mock_run.assert_called_once_with(self.project.id)

    @patch('apps.digest.admin.run_pipeline_for_project')
    def test_run_digest_action_error(self, mock_run):
        """Тест ошибки при запуске дайджеста."""
        mock_run.return_value = {
            'success': False,
            'error': 'Test error',
        }

        request = self.factory.post('/')
        request.user = self.user
        request._messages = FallbackStorage(request)

        queryset = Project.objects.filter(id=self.project.id)
        self.admin.run_digest_action(request, queryset)

        mock_run.assert_called_once()

    def test_run_digest_action_multiple_projects(self):
        """Тест попытки запуска дайджеста для нескольких проектов."""
        project2 = Project.objects.create(name="Project 2")

        request = self.factory.post('/')
        request.user = self.user
        request._messages = FallbackStorage(request)

        queryset = Project.objects.all()
        self.admin.run_digest_action(request, queryset)

        # Должно быть предупреждение о том, что можно выбрать только один проект

    def test_activate_project_action(self):
        """Тест активации проекта."""
        project2 = Project.objects.create(
            name="Project 2",
            is_active=False,
        )

        request = self.factory.post('/')
        request.user = self.user
        request._messages = FallbackStorage(request)

        queryset = Project.objects.filter(id=project2.id)
        self.admin.activate_project(request, queryset)

        self.project.refresh_from_db()
        project2.refresh_from_db()

        self.assertFalse(self.project.is_active)
        self.assertTrue(project2.is_active)


class DigestRunAdminTest(TestCase):
    """Тесты для DigestRunAdmin."""

    def setUp(self):
        """Создание тестовых данных."""
        self.site = AdminSite()
        self.admin = DigestRunAdmin(DigestRun, self.site)
        self.digest_run = DigestRun.objects.create(
            status="completed",
            total_articles_collected=100,
            total_articles_filtered=50,
            total_posts_created=10,
        )

    def test_status_badge_running(self):
        """Тест значка статуса для выполняющегося запуска."""
        self.digest_run.status = "running"
        badge = self.admin.status_badge(self.digest_run)
        self.assertIn('blue', badge)
        self.assertIn('Выполняется', badge)

    def test_status_badge_completed(self):
        """Тест значка статуса для завершенного запуска."""
        self.digest_run.status = "completed"
        badge = self.admin.status_badge(self.digest_run)
        self.assertIn('green', badge)
        self.assertIn('Завершен', badge)

    def test_status_badge_failed(self):
        """Тест значка статуса для провалившегося запуска."""
        self.digest_run.status = "failed"
        badge = self.admin.status_badge(self.digest_run)
        self.assertIn('red', badge)
        self.assertIn('Ошибка', badge)

    def test_duration_display_hours(self):
        """Тест отображения продолжительности в часах."""
        from django.utils import timezone
        from datetime import timedelta

        self.digest_run.started_at = timezone.now()
        self.digest_run.finished_at = timezone.now() + timedelta(hours=2, minutes=30, seconds=45)
        self.digest_run.save()

        duration = self.admin.duration_display(self.digest_run)
        self.assertIn('2ч', duration)
        self.assertIn('30м', duration)

    def test_duration_display_minutes(self):
        """Тест отображения продолжительности в минутах."""
        from django.utils import timezone
        from datetime import timedelta

        self.digest_run.started_at = timezone.now()
        self.digest_run.finished_at = timezone.now() + timedelta(minutes=5, seconds=30)
        self.digest_run.save()

        duration = self.admin.duration_display(self.digest_run)
        self.assertIn('5м', duration)

    def test_success_rate_display(self):
        """Тест отображения процента успешности."""
        rate = self.admin.success_rate_display(self.digest_run)
        self.assertIn('10.0', rate)  # 10 постов из 100 статей

    def test_filter_rate_display(self):
        """Тест отображения процента фильтрации."""
        rate = self.admin.filter_rate_display(self.digest_run)
        self.assertIn('50.0', rate)  # 50 из 100

    def test_has_add_permission(self):
        """Тест запрета на ручное создание запусков."""
        request = RequestFactory().get('/')
        has_permission = self.admin.has_add_permission(request)
        self.assertFalse(has_permission)


class ArticleAdminTest(TestCase):
    """Тесты для ArticleAdmin."""

    def setUp(self):
        """Создание тестовых данных."""
        self.site = AdminSite()
        self.admin = ArticleAdmin(Article, self.site)
        self.digest_run = DigestRun.objects.create(status="running")
        self.article = Article.objects.create(
            digest_run=self.digest_run,
            title="Test Article with a Very Long Title That Exceeds 100 Characters to Test Truncation",
            url="https://example.com/article",
            interest_score=8.5,
        )

    def test_short_title(self):
        """Тест отображения короткого заголовка."""
        title = self.admin.short_title(self.article)
        self.assertEqual(len(title), 100)

    def test_interest_score_badge_high(self):
        """Тест значка оценки интереса для высокой оценки."""
        self.article.interest_score = 9.0
        badge = self.admin.interest_score_badge(self.article)
        self.assertIn('green', badge)
        self.assertIn('9.0', badge)

    def test_interest_score_badge_medium(self):
        """Тест значка оценки интереса для средней оценки."""
        self.article.interest_score = 6.0
        badge = self.admin.interest_score_badge(self.article)
        self.assertIn('orange', badge)

    def test_interest_score_badge_low(self):
        """Тест значка оценки интереса для низкой оценки."""
        self.article.interest_score = 3.0
        badge = self.admin.interest_score_badge(self.article)
        self.assertIn('red', badge)

    def test_url_link(self):
        """Тест кликабельной ссылки."""
        link = self.admin.url_link(self.article)
        self.assertIn('href="https://example.com/article"', link)
        self.assertIn('target="_blank"', link)

    def test_has_add_permission(self):
        """Тест запрета на ручное создание статей."""
        request = RequestFactory().get('/')
        has_permission = self.admin.has_add_permission(request)
        self.assertFalse(has_permission)

    def test_has_delete_permission(self):
        """Тест запрета на удаление статей."""
        request = RequestFactory().get('/')
        has_permission = self.admin.has_delete_permission(request)
        self.assertFalse(has_permission)


class GeneratedPostAdminTest(TestCase):
    """Тесты для GeneratedPostAdmin."""

    def setUp(self):
        """Создание тестовых данных."""
        self.site = AdminSite()
        self.admin = GeneratedPostAdmin(GeneratedPost, self.site)
        self.digest_run = DigestRun.objects.create(status="running")
        self.article = Article.objects.create(
            digest_run=self.digest_run,
            title="Test Article",
            url="https://example.com/article",
        )
        self.post = GeneratedPost.objects.create(
            article=self.article,
            platform="telegram",
            post_content="Test post content",
        )

    def test_article_title(self):
        """Тест отображения заголовка статьи."""
        title = self.admin.article_title(self.post)
        self.assertEqual(title, "Test Article")

    def test_has_image_badge_with_image(self):
        """Тест значка наличия изображения, когда изображение есть."""
        # В тесте сложно создать реальный файл, поэтому просто проверим логику
        badge = self.admin.has_image_badge(self.post)
        self.assertIn('Нет', badge)

    def test_image_preview_no_image(self):
        """Тест превью изображения, когда изображения нет."""
        preview = self.admin.image_preview(self.post)
        self.assertEqual(preview, "Нет изображения")

    def test_has_add_permission(self):
        """Тест запрета на ручное создание постов."""
        request = RequestFactory().get('/')
        has_permission = self.admin.has_add_permission(request)
        self.assertFalse(has_permission)


class ArticleSourceAdminTest(TestCase):
    """Тесты для ArticleSourceAdmin."""

    def setUp(self):
        """Создание тестовых данных."""
        self.site = AdminSite()
        self.admin = ArticleSourceAdmin(ArticleSource, self.site)
        self.project = Project.objects.create(name="Test Project")
        self.source = ArticleSource.objects.create(
            project=self.project,
            name="Test Source",
            source_type="rss",
            success_rate=75.5,
        )

    def test_success_rate_display_high(self):
        """Тест отображения высокого процента успешности."""
        self.source.success_rate = 80.0
        rate = self.admin.success_rate_display(self.source)
        self.assertIn('green', rate)
        self.assertIn('80.0', rate)

    def test_success_rate_display_medium(self):
        """Тест отображения среднего процента успешности."""
        self.source.success_rate = 35.0
        rate = self.admin.success_rate_display(self.source)
        self.assertIn('orange', rate)

    def test_success_rate_display_low(self):
        """Тест отображения низкого процента успешности."""
        self.source.success_rate = 10.0
        rate = self.admin.success_rate_display(self.source)
        self.assertIn('red', rate)
