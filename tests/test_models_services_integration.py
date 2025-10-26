#!/usr/bin/env python
"""
Тестовый скрипт для проверки интеграции моделей и сервисов.
"""

import os
import sys
import django
from pathlib import Path

# Добавляем путь к проекту в sys.path
project_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(project_dir))

# Устанавливаем переменную окружения для Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Инициализируем Django
django.setup()

from loguru import logger
from apps.digest.services.integration_service import IntegrationService
from apps.digest.models import (
    DigestRun,
    NewsSource,
    Article,
    GeneratedPost,
    Configuration,
    Keyword,
)


def test_models_services_integration():
    """Тест интеграции моделей и сервисов."""
    logger.info("🚀 Запуск теста интеграции моделей и сервисов")

    try:
        # Создаем интеграционный сервис
        integration_service = IntegrationService()

        # Тест 1: Создание запуска дайджеста
        logger.info("Тест 1: Создание запуска дайджеста")
        digest_run = integration_service.create_digest_run()
        print(f"✅ Создан запуск дайджеста: {digest_run.id}")

        # Тест 2: Обновление статистики запуска
        logger.info("Тест 2: Обновление статистики запуска")
        integration_service.update_digest_run_stats(
            digest_run,
            total_collected=10,
            total_filtered=5,
            total_posts=3,
            total_images=2,
            status="completed",
        )
        print(f"✅ Обновлена статистика запуска: {digest_run.id}")

        # Тест 3: Получение или создание источника новостей
        logger.info("Тест 3: Получение или создание источника новостей")
        source = integration_service.get_or_create_news_source(
            "Тестовый источник", "https://test.com", "manual"
        )
        print(f"✅ Источник новостей: {source.name}")

        # Тест 4: Сохранение статей
        logger.info("Тест 4: Сохранение статей")
        test_articles = [
            {
                "title": "Тестовая статья 1",
                "url": "https://test.com/article1",
                "summary": "Краткое содержание статьи 1",
                "content_type": "news",
                "interest_score": 8.5,
                "is_relevant": True,
                "relevance_reason": "Релевантна",
                "interest_reason": "Интересна",
                "source": "Тестовый источник",
            },
            {
                "title": "Тестовая статья 2",
                "url": "https://test.com/article2",
                "summary": "Краткое содержание статьи 2",
                "content_type": "tutorial",
                "interest_score": 7.2,
                "is_relevant": True,
                "relevance_reason": "Релевантна",
                "interest_reason": "Полезна",
                "source": "Тестовый источник",
            },
        ]

        saved_articles = integration_service.save_articles_to_db(
            digest_run, test_articles, source
        )
        print(f"✅ Сохранено статей: {len(saved_articles)}")

        # Тест 5: Сохранение постов
        logger.info("Тест 5: Сохранение постов")
        test_posts = [
            {
                "title": "Тестовая статья 1",
                "url": "https://test.com/article1",
                "post_content": "Текст поста 1",
                "image_idea": "Идея для изображения 1",
                "image_path": "/path/to/image1.png",
            }
        ]

        saved_posts = integration_service.save_generated_posts(test_posts)
        print(f"✅ Сохранено постов: {len(saved_posts)}")

        # Тест 6: Получение конфигурации
        logger.info("Тест 6: Получение конфигурации")
        # Создаем тестовую конфигурацию, если её нет
        if not Configuration.objects.filter(is_active=True).exists():
            config = Configuration.objects.create(
                name="Тестовая конфигурация",
                flowise_host="http://localhost:3000",
                flowise_filter_id="test_filter",
                flowise_copywriter_id="test_copywriter",
                is_active=True,
            )
            print(f"✅ Создана тестовая конфигурация: {config.name}")

        config = integration_service.get_active_configuration()
        if config:
            print(f"✅ Активная конфигурация: {config.name}")
        else:
            print("❌ Активная конфигурация не найдена")

        # Тест 7: Получение ключевых слов
        logger.info("Тест 7: Получение ключевых слов")
        # Создаем тестовые ключевые слова, если их нет
        if not Keyword.objects.filter(is_active=True).exists():
            keywords_list = ["Python", "Django", "AI", "machine learning"]
            for kw in keywords_list:
                Keyword.objects.get_or_create(keyword=kw, defaults={"is_active": True})
            print("✅ Созданы тестовые ключевые слова")

        keywords = integration_service.get_active_keywords()
        print(f"✅ Активные ключевые слова: {keywords}")

        # Тест 8: Проверка сохраненных данных в базе
        logger.info("Тест 8: Проверка сохраненных данных в базе")
        total_runs = DigestRun.objects.count()
        total_sources = NewsSource.objects.count()
        total_articles = Article.objects.count()
        total_posts = GeneratedPost.objects.count()

        print("📊 Статистика в базе данных:")
        print(f"   - Запусков дайджеста: {total_runs}")
        print(f"   - Источников новостей: {total_sources}")
        print(f"   - Статей: {total_articles}")
        print(f"   - Постов: {total_posts}")

        logger.info("✅ Тест интеграции моделей и сервисов успешно завершен")

    except Exception as e:
        logger.error(f"❌ Ошибка во время теста: {e}")
        raise


if __name__ == "__main__":
    test_models_services_integration()
