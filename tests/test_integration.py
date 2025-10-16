#!/usr/bin/env python
"""
Скрипт для тестирования интеграции сервисов с моделями Django.
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
from apps.digest.models import DigestRun


def test_integration():
    logger.info("🚀 Запуск теста интеграции сервисов с моделями")

    # Создаем интеграционный сервис
    integration_service = IntegrationService()

    # Тестируем создание запуска дайджеста
    logger.info("Тест: Создание запуска дайджеста")
    digest_run = integration_service.create_digest_run()
    print(f"Создан запуск: {digest_run.id}")

    # Тестируем обновление статистики
    logger.info("Тест: Обновление статистики запуска")
    integration_service.update_digest_run_stats(
        digest_run,
        total_collected=10,
        total_filtered=3,
        total_posts=3,
        total_images=2,
        status="completed",
    )
    print(f"Обновлена статистика для запуска: {digest_run.id}")

    # Тестируем получение или создание источника новостей
    logger.info("Тест: Получение или создание источника новостей")
    source = integration_service.get_or_create_news_source(
        "Тестовый источник", "https://test.com", "manual"
    )
    print(f"Источник: {source.name}")

    # Тестируем сохранение статей
    logger.info("Тест: Сохранение статей")
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
        },
    ]

    saved_articles = integration_service.save_articles_to_db(
        digest_run, test_articles, source
    )
    print(f"Сохранено статей: {len(saved_articles)}")

    # Тестируем сохранение постов
    logger.info("Тест: Сохранение постов")
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
    print(f"Сохранено постов: {len(saved_posts)}")

    # Тестируем получение конфигурации
    logger.info("Тест: Получение конфигурации")
    config = integration_service.get_active_configuration()
    if config:
        print(f"Активная конфигурация: {config.name}")
    else:
        print("Активная конфигурация не найдена")

    # Тестируем получение ключевых слов
    logger.info("Тест: Получение ключевых слов")
    keywords = integration_service.get_active_keywords()
    print(f"Активные ключевые слова: {keywords}")

    logger.info("✅ Тест интеграции успешно завершен")

    # Выводим статистику из базы данных
    total_runs = DigestRun.objects.count()
    print(f"Всего запусков в базе: {total_runs}")


if __name__ == "__main__":
    test_integration()
