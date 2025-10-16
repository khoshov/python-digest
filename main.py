#!/usr/bin/env python3
"""
Отдельный скрипт для запуска полного pipeline SMM Agents.

Этот скрипт содержит полную цепочку обработки новостей:
1. Scout - сбор новостей из RSS лент и Google Custom Search
2. Filter - фильтрация релевантных новостей через Flowise
3. Copywriter - создание постов из отфильтрованных новостей
4. Image Generator - генерация изображений через OpenAI DALL-E

Запуск: python run_pipeline.py
"""

import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Добавляем путь к проекту в sys.path для импорта модулей
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.pipeline import run_news_pipeline_with_tracking
from config import settings
from email_sender import send_email_notification, validate_email_configuration
from logger.logger import setup_logger

logger = setup_logger(module_name=__name__)


def print_banner():
    """Печатает баннер приложения."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                        🐍 PYTHON DIGEST                          ║
║                    Automated Content Pipeline                    ║
║                                                                  ║
║  Scout → Filter → Copywriter → Image Generator → Email           ║
║                                                                  ║
║           Для Python-разработчиков • Каждую неделю               ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def validate_configuration() -> bool:
    """
    Проверяет конфигурацию перед запуском pipeline.

    Returns:
        bool: True если конфигурация корректна
    """
    logger.info("🔧 Проверяем конфигурацию...")

    # Обязательные настройки
    required_settings = {
        "flowise_host": settings.flowise_host,
        "flowise_filter_id": settings.flowise_filter_id,
        "flowise_copywriter_id": settings.flowise_copywriter_id,
    }

    missing = []
    for key, value in required_settings.items():
        if not value:
            missing.append(key)

    if missing:
        logger.error(f"❌ Отсутствуют обязательные настройки: {', '.join(missing)}")
        return False

    # Проверяем источники новостей
    has_google = (
        settings.enable_google_news
        and settings.google_api_key
        and settings.google_cse_id
    )
    has_rss = settings.enable_rss_news

    if not has_google and not has_rss:
        logger.error("❌ Не настроен ни один источник новостей!")
        logger.error(
            "   - Для Google News нужны: GOOGLE_API_KEY, GOOGLE_CSE_ID, ENABLE_GOOGLE_NEWS=True"
        )
        logger.error("   - Для RSS нужно: ENABLE_RSS_NEWS=True")
        return False

    # Проверяем настройки изображений
    if settings.generate_images and not settings.openai_api_key:
        logger.warning("⚠️ Генерация изображений включена, но не указан OPENAI_API_KEY")
        logger.warning("   Изображения создаваться не будут")

    # Проверяем настройки email
    if not validate_email_configuration():
        return False

    logger.info("✅ Конфигурация проверена")
    return True


def print_configuration_summary():
    """Выводит сводку по конфигурации."""
    logger.info("📋 Сводка по конфигурации:")
    logger.info(f"   • Flowise Host: {settings.flowise_host}")

    # Источники новостей
    sources = []
    if (
        settings.enable_google_news
        and settings.google_api_key
        and settings.google_cse_id
    ):
        sources.append("Google Custom Search")
    if settings.enable_rss_news:
        sources.append(f"RSS (период: {settings.rss_hours_period}ч)")

    logger.info(f"   • Источники новостей: {', '.join(sources) if sources else 'НЕТ'}")

    # Генерация изображений
    if settings.generate_images and settings.openai_api_key:
        logger.info("   • Генерация изображений: ✅ включена (OpenAI DALL-E)")
    else:
        logger.info("   • Генерация изображений: ❌ отключена")

    # Email уведомления
    if settings.enable_email_sending and settings.email_recipients:
        logger.info(
            f"   • Email уведомления: ✅ включены ({len(settings.email_recipients)} получателей)"
        )
    else:
        logger.info("   • Email уведомления: ❌ отключены")


def get_default_keywords() -> List[str]:
    """
    Возвращает список ключевых слов по умолчанию для поиска Python-контента.

    Returns:
        List[str]: Ключевые слова
    """
    return [
        "Python",
        "Django",
        "Flask",
        "FastAPI",
        "pandas",
        "numpy",
        "pytest",
        "asyncio",
        "машинное обучение Python",
        "Python разработка",
        "Python инструменты",
        "Python библиотеки",
        "Python фреймворки",
        "Python обучение",
        "Python мемы",
        "Python история",
    ]


def get_default_rss_feeds() -> List[str]:
    """
    Возвращает список RSS лент по умолчанию для Python контента.

    Returns:
        List[str]: RSS ленты
    """
    return [
        # Python-специфичные источники
        "https://habr.com/ru/rss/hub/python/",
        "https://habr.com/ru/rss/hub/django/",
        "https://habr.com/ru/rss/all/all/?fl=ru",
        "https://tproger.ru/feed/",
        "https://realpython.com/atom.xml",
        "https://pythondigest.ru/rss/",
        "https://planetpython.org/rss20.xml",
        "https://pyfound.blogspot.com/feeds/posts/default",
        "https://www.blog.pythonlibrary.org/feed/",
        # GitHub и разработка
        "https://github.blog/feed/",
        "https://stackoverflow.com/feeds/tag?tagnames=python&sort=newest",
        # Дополнительные технические источники
        "https://hynek.me/articles/atom.xml",
        "https://hackaday.com/feed/",
        # Reddit Python сообщества (если доступны RSS)
        # "https://www.reddit.com/r/Python/.rss",
        # "https://www.reddit.com/r/learnpython/.rss",
    ]


def create_image_config() -> Dict:
    """
    Создает конфигурацию для генерации изображений.

    Returns:
        Dict: Конфигурация изображений
    """
    return {
        "enabled": settings.generate_images and bool(settings.openai_api_key),
        "openai_api_key": settings.openai_api_key,
    }


def save_results_summary(results: List[Dict[str, str]], output_dir: Path):
    """
    Сохраняет краткую сводку результатов.

    Args:
        results: Результаты pipeline
        output_dir: Директория для сохранения
    """
    if not results:
        return

    summary_file = (
        output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Python Digest Pipeline Summary\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total posts: {len(results)}\n")
        f.write("=" * 50 + "\n\n")

        for idx, post in enumerate(results, 1):
            f.write(f"{idx}. {post['title']}\n")
            f.write(f"   URL: {post['url']}\n")
            f.write(f"   Has image: {'Yes' if post.get('image_path') else 'No'}\n")
            f.write(f"   Post length: {len(post.get('post_content', ''))} chars\n")
            f.write("\n")

    logger.info(f"📄 Сводка сохранена: {summary_file}")


def save_comprehensive_report(
    all_news: List[Dict[str, str]],
    filtered_news: List[Dict[str, str]],
    final_posts: List[Dict[str, str]],
    output_dir: Path,
    timestamp: str,
):
    """
    Сохраняет подробный отчет со всеми новостями и их статусами фильтрации.

    Args:
        all_news: Все собранные новости (Scout)
        filtered_news: Новости прошедшие фильтр (Filter)
        final_posts: Финальные посты с контентом (Copywriter)
        output_dir: Директория для сохранения
        timestamp: Временная метка
    """
    report_file = output_dir / f"comprehensive_report_{timestamp}.md"

    # Создаем множества URL для быстрого поиска
    filtered_urls = {news["url"] for news in filtered_news}
    final_urls = {post["url"] for post in final_posts}

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# 🐍 Python Digest - Подробный отчет\n\n")
        f.write(
            f"**Дата создания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        # Статистика
        f.write("## 📊 Статистика\n\n")
        f.write(f"- **Всего собрано новостей:** {len(all_news)}\n")
        f.write(
            f"- **Прошло фильтрацию:** {len(filtered_news)} ({len(filtered_news) / len(all_news) * 100:.1f}%)\n"
            if all_news
            else ""
        )
        f.write(f"- **Выбрано ТОП-8 самых интересных:** {min(8, len(filtered_news))}\n")
        f.write(f"- **Создано постов:** {len(final_posts)}\n")
        f.write(f"- **Отклонено фильтром:** {len(all_news) - len(filtered_news)}\n\n")

        # Информация о сортировке
        if filtered_news:
            top_score = max(
                (
                    news.get("filter_result", {}).get("interest_score", 0)
                    for news in filtered_news
                ),
                default=0,
            )
            bottom_score = min(
                (
                    news.get("filter_result", {}).get("interest_score", 0)
                    for news in filtered_news
                ),
                default=0,
            )
            f.write(
                f"**📈 Диапазон оценок отфильтрованных статей:** {bottom_score}/10 - {top_score}/10\n\n"
            )

        if final_posts:
            final_scores = [post.get("interest_score", 0) for post in final_posts]
            if final_scores:
                f.write(
                    f"**⭐ Оценки финальных постов:** {max(final_scores)}/10 - {min(final_scores)}/10 (отсортированы по убыванию)\n\n"
                )

        # Все новости с статусами
        f.write("## 📋 Все собранные новости\n\n")
        f.write(
            "| # | Статус | Оценка | Тип | Источник | Заголовок | Причина фильтрации | URL |\n"
        )
        f.write(
            "|---|--------|--------|-----|----------|-----------|-------------------|-----|\n"
        )

        for idx, news in enumerate(all_news, 1):
            # Определяем статус
            if news["url"] in final_urls:
                status = "✅ **ОПУБЛИКОВАН**"
            elif news["url"] in filtered_urls:
                status = "🔄 Отфильтрован"
            else:
                status = "❌ Отклонен"

            # Получаем данные фильтрации
            filter_result = news.get("filter_result", {})
            interest_score = filter_result.get("interest_score", 0)
            content_type = filter_result.get("content_type", "Неизвестно")
            relevance_reason = filter_result.get("relevance_reason", "Нет данных")
            interest_reason = filter_result.get("interest_reason", "Нет данных")

            # Формируем причину фильтрации
            if filter_result.get("is_relevant"):
                filter_reason = f"✅ {relevance_reason} | 🎯 {interest_reason}"
            else:
                filter_reason = f"❌ {relevance_reason}"

            # Определяем источник
            source = news.get("source", "Неизвестно")

            # Обрезаем заголовок если слишком длинный
            title = (
                news["title"][:80] + "..." if len(news["title"]) > 80 else news["title"]
            )
            title = title.replace(
                "|", "\\|"
            )  # Экранируем вертикальные черты для Markdown

            # Обрезаем причину фильтрации
            filter_reason = (
                filter_reason[:100] + "..."
                if len(filter_reason) > 100
                else filter_reason
            )
            filter_reason = filter_reason.replace("|", "\\|")

            f.write(
                f"| {idx} | {status} | {interest_score}/10 | {content_type} | {source} | {title} | {filter_reason} | [Ссылка]({news['url']}) |\n"
            )

        f.write("\n")

        # ТОП-8 финальных постов
        if final_posts:
            f.write(
                "## 🏆 ТОП-8 самых интересных постов (отсортированы по убыванию интереса)\n\n"
            )
            for idx, post in enumerate(final_posts, 1):
                interest_score = post.get("interest_score", 0)
                content_type = post.get("content_type", "Неизвестно")
                interest_reason = post.get("filter_result", {}).get(
                    "interest_reason", "Нет объяснения"
                )

                f.write(f"### {idx}. {post['title']} `[{interest_score}/10]`\n\n")
                f.write(f"**🔗 URL:** {post['url']}\n\n")
                f.write(f"**📊 Оценка интереса:** {interest_score}/10\n\n")
                f.write(f"**📚 Тип контента:** {content_type}\n\n")
                f.write(f"**🎯 Почему интересно:** {interest_reason}\n\n")

                if post.get("summary"):
                    f.write(f"**📝 Краткое содержание:** {post['summary']}\n\n")

                if post.get("post_content"):
                    f.write(
                        f"**✍️ Созданный пост:**\n```\n{post['post_content']}\n```\n\n"
                    )

                if post.get("image_path"):
                    f.write(f"**🖼️ Изображение:** {post['image_path']}\n\n")

                f.write("---\n\n")

        # Статистика по оценкам фильтра
        f.write("## 📊 Статистика оценок фильтра\n\n")
        scores = [
            news.get("filter_result", {}).get("interest_score", 0) for news in all_news
        ]
        avg_score = sum(scores) / len(scores) if scores else 0
        high_scores = len([s for s in scores if s >= 8])
        medium_scores = len([s for s in scores if 5 <= s < 8])
        low_scores = len([s for s in scores if s < 5])

        f.write(f"- **Средняя оценка интереса:** {avg_score:.1f}/10\n")
        f.write(f"- **Высокие оценки (8-10):** {high_scores}\n")
        f.write(f"- **Средние оценки (5-7):** {medium_scores}\n")
        f.write(f"- **Низкие оценки (0-4):** {low_scores}\n\n")

        # Статистика по типам контента
        f.write("## 📚 Статистика по типам контента\n\n")
        content_types = {}
        for news in all_news:
            content_type = news.get("filter_result", {}).get(
                "content_type", "Неизвестно"
            )
            content_types[content_type] = content_types.get(content_type, 0) + 1

        f.write("| Тип контента | Количество |\n")
        f.write("|--------------|------------|\n")
        for content_type, count in sorted(
            content_types.items(), key=lambda x: x[1], reverse=True
        ):
            f.write(f"| {content_type} | {count} |\n")
        f.write("\n")

        # Статистика по источникам
        f.write("## 📡 Статистика по источникам\n\n")
        source_stats = {}
        for news in all_news:
            source = news.get("source", "Неизвестно")
            if source not in source_stats:
                source_stats[source] = {
                    "total": 0,
                    "filtered": 0,
                    "published": 0,
                    "avg_score": 0,
                }
            source_stats[source]["total"] += 1
            if news["url"] in filtered_urls:
                source_stats[source]["filtered"] += 1
            if news["url"] in final_urls:
                source_stats[source]["published"] += 1

            # Добавляем к средней оценке
            score = news.get("filter_result", {}).get("interest_score", 0)
            source_stats[source]["avg_score"] += score

        f.write(
            "| Источник | Собрано | Отфильтровано | Опубликовано | Ср. оценка | Эффективность |\n"
        )
        f.write(
            "|----------|---------|---------------|--------------|------------|---------------|\n"
        )

        for source, stats in sorted(source_stats.items()):
            efficiency = (
                (stats["published"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            avg_source_score = (
                stats["avg_score"] / stats["total"] if stats["total"] > 0 else 0
            )
            f.write(
                f"| {source} | {stats['total']} | {stats['filtered']} | {stats['published']} | {avg_source_score:.1f}/10 | {efficiency:.1f}% |\n"
            )

    logger.info(f"📊 Подробный отчет сохранен: {report_file}")


def main():
    """Основная функция запуска pipeline."""
    # Настройка
    setup_logging()
    print_banner()

    logger.info("🚀 Запуск Python Digest Pipeline")

    # Проверяем конфигурацию
    if not validate_configuration():
        logger.error("❌ Невозможно запустить pipeline из-за ошибок конфигурации")
        sys.exit(1)

    print_configuration_summary()

    # Подготавливаем параметры
    keywords = get_default_keywords()

    # Настраиваем источники новостей
    google_api = settings.google_api_key if settings.enable_google_news else None
    google_cse = settings.google_cse_id if settings.enable_google_news else None
    rss_feeds = get_default_rss_feeds() if settings.enable_rss_news else None

    # Конфигурация изображений
    image_config = create_image_config()

    # Создаем выходную директорию
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)

    # Генерируем имя файла с текущей датой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file = output_dir / f"news_digest_{timestamp}.md"

    logger.info(f"📂 Результаты будут сохранены в: {markdown_file}")
    logger.info("=" * 60)

    try:
        # Запускаем полную цепочку с отслеживанием
        pipeline_results = run_news_pipeline_with_tracking(
            keywords=keywords,
            flowise_host=settings.flowise_host,
            flowise_filter_id=settings.flowise_filter_id,
            flowise_copywriter_id=settings.flowise_copywriter_id,
            google_api=google_api,
            google_cse=google_cse,
            rss_feeds=rss_feeds,
            rss_hours=settings.rss_hours_period,
            max_per_source=20,  # Собираем больше, чтобы было из чего выбирать ТОП-8
            image_config=image_config,
            save_to_markdown=True,
            markdown_file=str(markdown_file),
        )

        # Извлекаем результаты
        all_news = pipeline_results["all_news"]
        filtered_news = pipeline_results["filtered_news"]
        final_posts = pipeline_results["final_posts"]

        # Создаем подробный отчет
        comprehensive_report_file = output_dir / f"comprehensive_report_{timestamp}.md"
        save_comprehensive_report(
            all_news, filtered_news, final_posts, output_dir, timestamp
        )

        # Обрабатываем результаты
        if final_posts:
            logger.success("🎉 Pipeline завершен успешно!")
            logger.success(
                f"📊 Создано {len(final_posts)} готовых постов (ТОП-{len(final_posts)} самых интересных)"
            )

            # Статистика по изображениям
            posts_with_images = len([p for p in final_posts if p.get("image_path")])
            logger.info(
                f"🖼️ Постов с изображениями: {posts_with_images}/{len(final_posts)}"
            )

            # Сохраняем краткую сводку
            save_results_summary(final_posts, output_dir)

            # Отправляем email уведомление
            summary_file = output_dir / f"summary_{timestamp}.txt"
            email_sent = send_email_notification(
                posts=final_posts,
                markdown_file=markdown_file,
                summary_file=summary_file if summary_file.exists() else None,
                comprehensive_report=comprehensive_report_file
                if comprehensive_report_file.exists()
                else None,
            )

            if email_sent:
                logger.success("📧 Email уведомление отправлено успешно!")
            else:
                logger.warning(
                    "⚠️ Email уведомление не отправлено - проверьте настройки SMTP"
                )

            # Выводим краткую информацию о постах
            logger.info("\n📋 Созданные посты:")
            for idx, post in enumerate(final_posts, 1):
                logger.info(f"   {idx}. {post['title'][:60]}...")
                logger.info(f"      {post['url']}")
                if post.get("image_path"):
                    logger.info(f"      🖼️ {post['image_path']}")
                logger.info("")

        else:
            logger.warning("😔 Pipeline завершен, но постов не создано")
            logger.warning("💡 Проверьте настройки фильтрации и источники новостей")

            # Все равно создаем подробный отчет если есть собранные новости
            if all_news:
                save_comprehensive_report(
                    all_news, filtered_news, [], output_dir, timestamp
                )

            # Отправляем email уведомление даже если постов нет
            summary_file = output_dir / f"summary_{timestamp}.txt"
            email_sent = send_email_notification(
                posts=[],  # Пустой список постов
                markdown_file=None,
                summary_file=None,
                comprehensive_report=comprehensive_report_file
                if all_news and comprehensive_report_file.exists()
                else None,
            )

            if email_sent:
                logger.success("📧 Email уведомление отправлено успешно!")
            else:
                logger.warning(
                    "⚠️ Email уведомление не отправлено - проверьте настройки SMTP"
                )

    except KeyboardInterrupt:
        logger.warning("⚠️ Pipeline прерван пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в pipeline: {e}")
        logger.exception("Детали ошибки:")
        sys.exit(1)

    logger.info("✅ Программа завершена")


if __name__ == "__main__":
    main()
