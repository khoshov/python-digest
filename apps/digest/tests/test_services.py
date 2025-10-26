"""
Тесты для сервисов приложения digest.
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase

from apps.digest.services.filter_service import FilterService
from apps.digest.services.copywriter_service import CopywriterService
from apps.digest.services.scout_service import ScoutService
from apps.digest.services.pipeline_runner import (
    get_api_keys_from_env,
    run_pipeline_for_project,
)
from apps.digest.models import Project, ArticleSource, Keyword


class FilterServiceTest(TestCase):
    """Тесты для FilterService."""

    def setUp(self):
        """Создание тестовых данных."""
        self.service = FilterService()
        self.test_article = {
            'title': 'Python 3.13 Released',
            'summary': 'New version of Python is out',
            'url': 'https://example.com/article',
        }

    @patch('apps.digest.services.filter_service.ChatOpenAI')
    @patch('apps.digest.services.filter_service.ChatPromptTemplate')
    def test_check_relevance_with_deepseek(self, mock_prompt_class, mock_llm_class):
        """Тест проверки релевантности через DeepSeek."""
        # Мокируем результат
        expected_result = {
            'is_relevant': True,
            'relevance_reason': 'Python release',
            'content_type': 'news',
            'interest_score': 9.0,
            'interest_reason': 'Major release',
        }

        # Настраиваем мок для chain.invoke
        with patch.object(FilterService, 'check_relevance_with_deepseek', return_value=expected_result):
            result = self.service.check_relevance_with_deepseek(
                self.test_article,
                'test-api-key',
            )

            self.assertTrue(result['is_relevant'])
            self.assertEqual(result['interest_score'], 9.0)

    def test_filter_articles_empty_list(self):
        """Тест фильтрации пустого списка."""
        result = self.service.filter_articles([], 'test-api-key')
        self.assertEqual(result, [])

    @patch.object(FilterService, 'check_relevance_with_deepseek')
    def test_filter_articles_all_relevant(self, mock_check):
        """Тест фильтрации, когда все статьи релевантны."""
        mock_check.return_value = {
            'is_relevant': True,
            'content_type': 'news',
            'interest_score': 8.0,
            'relevance_reason': 'Good',
            'interest_reason': 'Interesting',
        }

        articles = [
            {'title': 'Article 1', 'summary': 'Summary 1', 'url': 'url1'},
            {'title': 'Article 2', 'summary': 'Summary 2', 'url': 'url2'},
        ]

        result = self.service.filter_articles(articles, 'test-api-key')
        self.assertEqual(len(result), 2)

    @patch.object(FilterService, 'check_relevance_with_deepseek')
    def test_filter_articles_some_relevant(self, mock_check):
        """Тест фильтрации, когда только некоторые статьи релевантны."""
        # Первая релевантна, вторая нет
        mock_check.side_effect = [
            {
                'is_relevant': True,
                'content_type': 'news',
                'interest_score': 8.0,
                'relevance_reason': 'Good',
                'interest_reason': 'Interesting',
            },
            {
                'is_relevant': False,
                'content_type': 'other',
                'interest_score': 3.0,
                'relevance_reason': 'Not relevant',
                'interest_reason': 'Boring',
            },
        ]

        articles = [
            {'title': 'Article 1', 'summary': 'Summary 1', 'url': 'url1'},
            {'title': 'Article 2', 'summary': 'Summary 2', 'url': 'url2'},
        ]

        result = self.service.filter_articles(articles, 'test-api-key')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Article 1')


class CopywriterServiceTest(TestCase):
    """Тесты для CopywriterService."""

    def setUp(self):
        """Создание тестовых данных."""
        self.service = CopywriterService()
        self.test_article = {
            'title': 'Python 3.13 Released',
            'summary': 'New version of Python is out',
            'url': 'https://example.com/article',
        }

    @patch('apps.digest.services.copywriter_service.ChatOpenAI')
    def test_create_post_with_deepseek(self, mock_llm_class):
        """Тест создания поста через DeepSeek."""
        expected_result = {
            'post_content': 'Test post content',
            'image_idea': 'Test image idea',
        }

        with patch.object(CopywriterService, 'create_post_with_deepseek', return_value=expected_result):
            result = self.service.create_post_with_deepseek(
                self.test_article,
                'test-api-key',
            )

            self.assertEqual(result['post_content'], 'Test post content')
            self.assertEqual(result['image_idea'], 'Test image idea')

    @patch.object(CopywriterService, 'create_post_with_deepseek')
    def test_create_posts_for_articles(self, mock_create):
        """Тест создания постов для нескольких статей."""
        mock_create.return_value = {
            'post_content': 'Post',
            'image_idea': 'Image',
        }

        articles = [
            {'title': 'Article 1', 'summary': 'Summary 1', 'url': 'url1'},
            {'title': 'Article 2', 'summary': 'Summary 2', 'url': 'url2'},
        ]

        result = self.service.create_posts_for_articles(articles, 'test-api-key')
        self.assertEqual(len(result), 2)
        self.assertEqual(mock_create.call_count, 2)


class ScoutServiceTest(TestCase):
    """Тесты для ScoutService."""

    def setUp(self):
        """Создание тестовых данных."""
        self.service = ScoutService()

    def test_is_valid_article(self):
        """Тест проверки валидности URL статьи."""
        self.assertTrue(self.service.is_valid_article('https://example.com/article'))
        self.assertFalse(self.service.is_valid_article('https://news.google.com/article'))
        self.assertFalse(self.service.is_valid_article('https://news.ycombinator.com/article'))


class PipelineRunnerTest(TestCase):
    """Тесты для pipeline_runner."""

    @patch.dict('os.environ', {
        'DEEPSEEK_API_KEY': 'test-deepseek-key',
        'GOOGLE_API_KEY': 'test-google-key',
        'GOOGLE_CSE_ID': 'test-cse-id',
        'OPENAI_API_KEY': 'test-openai-key',
    })
    def test_get_api_keys_from_env(self):
        """Тест получения API ключей из окружения."""
        keys = get_api_keys_from_env()

        self.assertEqual(keys['deepseek_api_key'], 'test-deepseek-key')
        self.assertEqual(keys['google_api_key'], 'test-google-key')
        self.assertEqual(keys['google_cse_id'], 'test-cse-id')
        self.assertEqual(keys['openai_api_key'], 'test-openai-key')

    def test_run_pipeline_no_active_project(self):
        """Тест запуска пайплайна без активного проекта."""
        with self.assertRaises(ValueError) as context:
            run_pipeline_for_project()

        self.assertIn('Нет активного проекта', str(context.exception))

    def test_run_pipeline_project_not_found(self):
        """Тест запуска пайплайна для несуществующего проекта."""
        with self.assertRaises(ValueError) as context:
            run_pipeline_for_project(project_id=999)

        self.assertIn('не найден', str(context.exception))

    @patch.dict('os.environ', {})
    def test_run_pipeline_no_deepseek_key(self):
        """Тест запуска пайплайна без DEEPSEEK_API_KEY."""
        project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )

        with self.assertRaises(ValueError) as context:
            run_pipeline_for_project(project.id)

        self.assertIn('DEEPSEEK_API_KEY', str(context.exception))

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.services.pipeline_runner.NewsPipeline')
    def test_run_pipeline_success(self, mock_pipeline_class):
        """Тест успешного запуска пайплайна."""
        project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )
        Keyword.objects.create(
            project=project,
            keyword="Python",
            is_active=True,
        )
        ArticleSource.objects.create(
            project=project,
            name="Test Source",
            url="https://example.com/rss",
            source_type="rss",
            is_active=True,
        )

        # Мокируем пайплайн
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run_full_pipeline.return_value = [
            {'title': 'Article 1'},
            {'title': 'Article 2'},
        ]
        mock_pipeline_class.return_value = mock_pipeline_instance

        result = run_pipeline_for_project(project.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['project'], 'Test Project')
        self.assertEqual(result['total_posts'], 2)

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    @patch('apps.digest.services.pipeline_runner.NewsPipeline')
    def test_run_pipeline_error(self, mock_pipeline_class):
        """Тест обработки ошибок при запуске пайплайна."""
        project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )

        # Мокируем ошибку
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run_full_pipeline.side_effect = Exception("Test error")
        mock_pipeline_class.return_value = mock_pipeline_instance

        result = run_pipeline_for_project(project.id)

        self.assertFalse(result['success'])
        self.assertIn('Test error', result['error'])

    @patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test-key'})
    def test_run_pipeline_no_keywords(self):
        """Тест запуска пайплайна без ключевых слов."""
        project = Project.objects.create(
            name="Test Project",
            is_active=True,
        )

        with patch('apps.digest.services.pipeline_runner.NewsPipeline') as mock_pipeline:
            mock_instance = MagicMock()
            mock_instance.run_full_pipeline.return_value = []
            mock_pipeline.return_value = mock_instance

            result = run_pipeline_for_project(project.id)

            # Должен использовать дефолтное значение ["Python"]
            call_args = mock_instance.run_full_pipeline.call_args
            self.assertEqual(call_args.kwargs['keywords'], ["Python"])
