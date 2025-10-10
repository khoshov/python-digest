from typing import List, Dict, Set
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from difflib import SequenceMatcher

from logger.logger import setup_logger

logger = setup_logger(module_name=__name__)



class DeduplicationService:
    """
    Модуль deduplicator - удаление дубликатов новостей.

    Осуществляет проверку на дублирование статей по URL и сходству содержания
    для предотвращения повторов в финальном дайджесте.
    """
    def normalize_url(self, url: str) -> str:
        """
        Нормализует URL для сравнения, удаляя UTM-параметры и другие tracking данные.

        Args:
            url: Исходный URL

        Returns:
            str: Нормализованный URL
        """
        try:
            parsed = urlparse(url)

            # Удаляем tracking параметры
            query_params = parse_qs(parsed.query)
            tracking_params = {
                'utm_campaign', 'utm_source', 'utm_medium', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source', 'campaign'
            }

            # Оставляем только не-tracking параметры
            clean_params = {k: v for k, v in query_params.items()
                        if k.lower() not in tracking_params}

            # Восстанавливаем URL без tracking параметров
            clean_query = urlencode(clean_params, doseq=True)
            normalized = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),
                parsed.params,
                clean_query,
                ''  # убираем fragment
            ))

            return normalized

        except Exception as e:
            logger.debug(f"Ошибка нормализации URL {url}: {e}")
            return url.lower().strip()


    def calculate_content_similarity(self, text1: str, text2: str) -> float:
        """
        Вычисляет сходство между двумя текстами.

        Args:
            text1: Первый текст
            text2: Второй текст

        Returns:
            float: Коэффициент сходства от 0 до 1
        """
        if not text1 or not text2:
            return 0.0

        # Нормализуем тексты для сравнения
        normalized1 = text1.lower().strip()
        normalized2 = text2.lower().strip()

        return SequenceMatcher(None, normalized1, normalized2).ratio()


    def find_duplicates(self, articles: List[Dict[str, str]],
                    similarity_threshold: float = 0.85,
                    check_content: bool = True) -> List[Dict[str, str]]:
        """
        Находит и удаляет дубликаты из списка статей.

        Args:
            articles: Список статей с полями title, url, summary
            similarity_threshold: Порог сходства для определения дубликатов (0-1)
            check_content: Проверять ли сходство содержания помимо URL

        Returns:
            List[Dict]: Список статей без дубликатов
        """
        if not articles:
            return []

        seen_urls: Set[str] = set()
        unique_articles: List[Dict[str, str]] = []
        duplicates_found = 0

        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '')
            summary = article.get('summary', '')

            # Нормализуем URL для проверки
            normalized_url = self.normalize_url(url)

            # Проверяем дубликаты по URL
            if normalized_url in seen_urls:
                duplicates_found += 1
                logger.debug(f"Дубликат по URL найден: {title[:50]}... ({url})")
                continue

            # Проверяем сходство содержания с уже добавленными статьями
            is_duplicate = False
            if check_content and unique_articles:
                for existing_article in unique_articles:
                    # Сравниваем заголовки
                    title_similarity = self.calculate_content_similarity(
                        title, existing_article.get('title', '')
                    )

                    # Сравниваем содержание
                    content_similarity = self.calculate_content_similarity(
                        summary, existing_article.get('summary', '')
                    )

                    # Если заголовок или содержание очень похожи - это дубликат
                    max_similarity = max(title_similarity, content_similarity)
                    if max_similarity >= similarity_threshold:
                        duplicates_found += 1
                        logger.debug(f"Дубликат по содержанию найден (сходство {max_similarity:.2f}): {title[:50]}...")
                        is_duplicate = True
                        break

            if not is_duplicate:
                seen_urls.add(normalized_url)
                unique_articles.append(article)

        logger.info(f"🔍 Дедупликация: удалено {duplicates_found} дубликатов из {len(articles)} статей")
        return unique_articles


    def deduplicate_articles(self, articles: List[Dict[str, str]],
                            similarity_threshold: float = 0.85,
                            check_content: bool = True) -> List[Dict[str, str]]:
        """
        Основная функция для удаления дубликатов из статей.

        Args:
            articles: Список статей
            similarity_threshold: Порог сходства для определения дубликатов
            check_content: Проверять ли сходство содержания

        Returns:
            List[Dict]: Уникальные статьи
        """
        logger.debug(f"Начинаем дедупликацию {len(articles)} статей")

        unique_articles = self.find_duplicates(
            articles=articles,
            similarity_threshold=similarity_threshold,
            check_content=check_content
        )

        removed_count = len(articles) - len(unique_articles)
        if removed_count > 0:
            logger.info(f"✅ Дедупликация завершена: {removed_count} дубликатов удалено, {len(unique_articles)} уникальных статей осталось")
        else:
            logger.info(f"✅ Дедупликация завершена: дубликатов не найдено, {len(unique_articles)} статей")

        return unique_articles