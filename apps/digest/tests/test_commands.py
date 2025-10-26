"""
Тесты для management команд приложения digest.
"""

from io import StringIO
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.digest.models import Project, Keyword, ArticleSource


class RunDigestCommandTest(TestCase):
    """Тесты для команды run_digest."""

    def setUp(self):
        """Создание тестовых данных."""
        self.project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )
        Keyword.objects.create(
            project=self.project,
            keyword="Python",
            is_active=True,
        )

    def test_list_projects_empty(self):
        """Тест отображения пустого списка проектов."""
        Project.objects.all().delete()

        out = StringIO()
        call_command('run_digest', '--list-projects', stdout=out)

        output = out.getvalue()
        self.assertIn('Проектов не найдено', output)

    def test_list_projects_with_data(self):
        """Тест отображения списка проектов."""
        project2 = Project.objects.create(
            name="Test Project 2",
            is_active=False,
        )

        out = StringIO()
        call_command('run_digest', '--list-projects', stdout=out)

        output = out.getvalue()
        self.assertIn('Test Project', output)
        self.assertIn('Test Project 2', output)
        self.assertIn('АКТИВНЫЙ', output)
        self.assertIn('неактивный', output)

    @patch.dict('os.environ', {})
    def test_run_without_api_key(self):
        """Тест запуска без DEEPSEEK_API_KEY."""
        with self.assertRaises(CommandError) as context:
            call_command('run_digest')

        self.assertIn('DEEPSEEK_API_KEY', str(context.exception))

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.management.commands.run_digest.run_pipeline_for_project')
    def test_run_success(self, mock_run):
        """Тест успешного запуска."""
        mock_run.return_value = {
            'success': True,
            'project': 'Test Project',
            'total_posts': 5,
        }

        out = StringIO()
        call_command('run_digest', stdout=out)

        output = out.getvalue()
        self.assertIn('завершен успешно', output)
        self.assertIn('Test Project', output)
        self.assertIn('5', output)

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.management.commands.run_digest.run_pipeline_for_project')
    def test_run_error(self, mock_run):
        """Тест запуска с ошибкой."""
        mock_run.return_value = {
            'success': False,
            'project': 'Test Project',
            'error': 'Test error message',
        }

        with self.assertRaises(CommandError) as context:
            call_command('run_digest')

        self.assertIn('Test error message', str(context.exception))

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.management.commands.run_digest.run_pipeline_for_project')
    def test_run_specific_project(self, mock_run):
        """Тест запуска для конкретного проекта."""
        mock_run.return_value = {
            'success': True,
            'project': 'Test Project',
            'total_posts': 3,
        }

        out = StringIO()
        call_command('run_digest', f'--project-id={self.project.id}', stdout=out)

        mock_run.assert_called_once_with(self.project.id)

    def test_run_without_active_project(self):
        """Тест запуска без активного проекта."""
        self.project.is_active = False
        self.project.save()

        with self.assertRaises(CommandError) as context:
            call_command('run_digest')

        self.assertIn('активного проекта', str(context.exception).lower())

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.management.commands.run_digest.run_pipeline_for_project')
    def test_run_unexpected_error(self, mock_run):
        """Тест обработки неожиданной ошибки."""
        mock_run.side_effect = Exception("Unexpected error")

        with self.assertRaises(CommandError) as context:
            call_command('run_digest')

        self.assertIn('Неожиданная ошибка', str(context.exception))

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.management.commands.run_digest.run_pipeline_for_project')
    def test_run_value_error(self, mock_run):
        """Тест обработки ValueError."""
        mock_run.side_effect = ValueError("Invalid value")

        with self.assertRaises(CommandError) as context:
            call_command('run_digest')

        self.assertIn('Invalid value', str(context.exception))

    def test_run_nonexistent_project(self):
        """Тест запуска для несуществующего проекта."""
        with self.assertRaises(CommandError):
            call_command('run_digest', '--project-id=999')


class CommandIntegrationTest(TestCase):
    """Интеграционные тесты для команд."""

    def setUp(self):
        """Создание полной тестовой конфигурации."""
        self.project = Project.objects.create(
            name="Integration Test Project",
            is_active=True,
            rss_hours_period=168,
            max_articles_per_source=20,
            max_final_posts=8,
            enable_rss_news=True,
            enable_google_news=False,
        )

        # Добавляем ключевые слова
        Keyword.objects.create(
            project=self.project,
            keyword="Python",
            is_active=True,
            priority=1,
        )
        Keyword.objects.create(
            project=self.project,
            keyword="Django",
            is_active=True,
            priority=2,
        )

        # Добавляем источники
        ArticleSource.objects.create(
            project=self.project,
            name="Python RSS",
            url="https://www.python.org/feeds/python.rss/",
            source_type="rss",
            is_active=True,
            priority=1,
        )

    def test_list_shows_complete_project_info(self):
        """Тест отображения полной информации о проекте."""
        out = StringIO()
        call_command('run_digest', '--list-projects', stdout=out)

        output = out.getvalue()
        self.assertIn('Integration Test Project', output)
        self.assertIn(str(self.project.id), output)
        self.assertIn('АКТИВНЫЙ', output)

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.services.digest_service.NewsPipeline.run_full_pipeline')
    def test_full_pipeline_run(self, mock_pipeline):
        """Тест полного запуска пайплайна."""
        mock_pipeline.return_value = [
            {'title': 'Article 1', 'post_content': 'Content 1'},
            {'title': 'Article 2', 'post_content': 'Content 2'},
        ]

        out = StringIO()
        call_command('run_digest', f'--project-id={self.project.id}', stdout=out)

        output = out.getvalue()
        self.assertIn('Запуск пайплайна', output)

        # Проверяем, что пайплайн был вызван с правильными параметрами
        call_args = mock_pipeline.call_args
        self.assertIn('Python', call_args.kwargs['keywords'])
        self.assertIn('Django', call_args.kwargs['keywords'])
        self.assertEqual(call_args.kwargs['rss_hours'], 168)
        self.assertEqual(call_args.kwargs['max_per_source'], 20)
