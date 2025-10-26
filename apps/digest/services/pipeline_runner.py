"""
Модуль для запуска пайплайна обработки новостей.

Этот модуль содержит функции для запуска пайплайна с настройками из проекта в БД.
"""

import os
from typing import Optional, Dict, List
from loguru import logger

from apps.digest.models import Project, DigestRun, ArticleSource
from apps.digest.services.digest_service import NewsPipeline


def get_api_keys_from_env() -> Dict[str, Optional[str]]:
    """
    Получает API ключи из переменных окружения.

    Returns:
        Dict: Словарь с API ключами
    """
    return {
        'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY'),
        'google_api_key': os.getenv('GOOGLE_API_KEY'),
        'google_cse_id': os.getenv('GOOGLE_CSE_ID'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
    }


def run_pipeline_for_project(project_id: Optional[int] = None) -> Dict[str, any]:
    """
    Запускает пайплайн для указанного проекта или активного проекта.

    Args:
        project_id: ID проекта (если None, берется активный проект)

    Returns:
        Dict: Результаты выполнения пайплайна

    Raises:
        ValueError: Если проект не найден или нет активного проекта
    """
    # Получаем проект
    if project_id:
        project = Project.objects.filter(id=project_id).first()
        if not project:
            raise ValueError(f"Проект с ID {project_id} не найден")
    else:
        project = Project.get_active()
        if not project:
            raise ValueError("Нет активного проекта. Создайте проект и активируйте его.")

    logger.info(f"🚀 Запуск пайплайна для проекта: {project.name}")

    # Получаем API ключи из окружения
    api_keys = get_api_keys_from_env()

    # Проверяем наличие обязательного DeepSeek API ключа
    if not api_keys['deepseek_api_key']:
        raise ValueError("DEEPSEEK_API_KEY не установлен в переменных окружения")

    # Получаем активные ключевые слова
    keywords = project.get_active_keywords()
    if not keywords:
        logger.warning("⚠️ Нет активных ключевых слов. Добавьте ключевые слова в админке.")
        keywords = ["Python"]  # Используем дефолтное значение

    logger.info(f"📝 Используем ключевые слова: {', '.join(keywords)}")

    # Получаем RSS источники
    rss_sources = project.get_rss_sources()
    rss_feeds = [source.url for source in rss_sources if source.url]

    if project.enable_rss_news and not rss_feeds:
        logger.warning("⚠️ RSS включен, но нет активных RSS источников. Добавьте источники в админке.")

    logger.info(f"📡 Найдено {len(rss_feeds)} RSS источников")

    # Создаем конфигурацию для изображений
    image_config = {
        'enabled': project.generate_images,
        'openai_api_key': api_keys['openai_api_key'],
    }

    # Создаем пайплайн с настройками из проекта
    pipeline = NewsPipeline(
        deepseek_api_key=api_keys['deepseek_api_key'],
        image_config=image_config,
        filter_system_prompt=project.filter_system_prompt,
        filter_user_prompt=project.filter_user_prompt,
        copywriter_system_prompt=project.copywriter_system_prompt,
        copywriter_user_prompt=project.copywriter_user_prompt,
    )

    # Запускаем полную цепочку
    try:
        final_articles = pipeline.run_full_pipeline(
            keywords=keywords,
            google_api=api_keys['google_api_key'] if project.enable_google_news else None,
            google_cse=api_keys['google_cse_id'] if project.enable_google_news else None,
            rss_feeds=rss_feeds if project.enable_rss_news else None,
            rss_hours=project.rss_hours_period,
            max_per_source=project.max_articles_per_source,
        )

        logger.info(f"✅ Пайплайн завершен успешно! Создано {len(final_articles)} постов")

        return {
            'success': True,
            'project': project.name,
            'total_posts': len(final_articles),
            'articles': final_articles,
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении пайплайна: {e}")
        return {
            'success': False,
            'project': project.name,
            'error': str(e),
        }


def run_pipeline_with_custom_prompts(
    project_id: Optional[int] = None,
    filter_system_prompt: Optional[str] = None,
    filter_user_prompt: Optional[str] = None,
    copywriter_system_prompt: Optional[str] = None,
    copywriter_user_prompt: Optional[str] = None,
) -> Dict[str, any]:
    """
    Запускает пайплайн с кастомными промптами.

    Args:
        project_id: ID проекта (если None, берется активный проект)
        filter_system_prompt: Кастомный system prompt для фильтра
        filter_user_prompt: Кастомный user prompt для фильтра
        copywriter_system_prompt: Кастомный system prompt для копирайтера
        copywriter_user_prompt: Кастомный user prompt для копирайтера

    Returns:
        Dict: Результаты выполнения пайплайна
    """
    # TODO: Реализовать передачу кастомных промптов в сервисы
    # Пока используем стандартные промпты из проекта
    return run_pipeline_for_project(project_id)
