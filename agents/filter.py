import requests
from typing import List, Dict
from loguru import logger


def check_relevance_with_flowise(article: Dict[str, str], flow_id: str, flowise_host: str) -> Dict[str, any]:
    url = f"{flowise_host}/api/v1/prediction/{flow_id}"

    filter_prompt = f"Заголовок: {article.get('title', '')} Краткое содержание: {article.get('summary', '')}"

    payload = {"question": filter_prompt}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        result_text = response.json().get("text", "").strip()

        # Логируем сырой ответ для отладки
        logger.debug(f"📥 Сырой ответ от Flowise для '{article.get('title', '')[:50]}...': {result_text[:500]}...")

        import json
        import re

        # Очищаем ответ от markdown блоков
        clean_text = result_text
        if "```json" in result_text:
            # Извлекаем JSON из markdown блока
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group(1)
                logger.debug(f"📄 Извлечен JSON из markdown блока: {clean_text[:200]}...")
        else:
            # Пытаемся найти JSON в тексте без markdown блоков
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group(0)
                logger.debug(f"📄 Найден JSON в тексте: {clean_text[:200]}...")

        try:
            result = json.loads(clean_text)

            # Новый формат ответа
            return {
                'is_relevant': result.get('is_relevant', False),
                'relevance_reason': result.get('relevance_reason', 'Нет объяснения'),
                'interest_score': result.get('interest_score', 0),
                'interest_reason': result.get('interest_reason', 'Нет объяснения'),
                'content_type': result.get('content_type', 'Неизвестно'),
                'summary': result.get('summary', ''),
                'title_ru': result.get('title_ru', ''),
                'url': result.get('url', article.get('url', ''))
            }
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Не удалось парсить JSON ответ для '{article.get('title', '')[:50]}...': {e}")
            logger.warning(f"📄 Исходный текст: {result_text[:1000]}...")
            logger.warning(f"🧹 Очищенный текст: {clean_text[:1000]}...")
            return {
                'is_relevant': False,
                'relevance_reason': f'Ошибка парсинга JSON: {str(e)[:100]}',
                'interest_score': 0,
                'interest_reason': 'Ошибка парсинга JSON ответа',
                'content_type': 'Ошибка',
                'summary': '',
                'title_ru': '',
                'url': article.get('url', '')
            }

    except Exception as e:
        logger.error(f"Ошибка при проверке релевантности через Flowise: {e}")
        return {
            'is_relevant': False,
            'relevance_reason': 'Ошибка API',
            'interest_score': 0,
            'interest_reason': 'Ошибка API',
            'content_type': 'Ошибка',
            'summary': '',
            'title_ru': '',
            'url': article.get('url', '')
        }


def filter_news_with_flowise(articles: List[Dict[str, str]],
                            flow_id: str,
                            flowise_host: str) -> List[Dict[str, str]]:

    filtered_articles = []

    for article in articles:
        relevance_check = check_relevance_with_flowise(article, flow_id, flowise_host)

        # Добавляем информацию о фильтрации к статье
        article_with_meta = article.copy()
        article_with_meta['filter_result'] = relevance_check

        if relevance_check['is_relevant']:
            # Используем данные от фильтра, если они есть
            if relevance_check['title_ru']:
                article_with_meta['title'] = relevance_check['title_ru']
            if relevance_check['summary']:
                article_with_meta['summary'] = relevance_check['summary']

            article_with_meta['content_type'] = relevance_check['content_type']
            article_with_meta['interest_score'] = relevance_check['interest_score']

            filtered_articles.append(article_with_meta)
            logger.debug(f"✓ Статья прошла фильтр: {article['title'][:50]}... (Оценка: {relevance_check['interest_score']}/10, Тип: {relevance_check['content_type']})")
        else:
            logger.debug(f"✗ Статья отклонена: {article['title'][:50]}... Причина: {relevance_check['relevance_reason']}")

    # Сортируем по оценке интереса (от высокой к низкой)
    filtered_articles.sort(key=lambda x: x.get('interest_score', 0), reverse=True)

    logger.info(f"📊 Отфильтрованные статьи отсортированы по интересности (от {filtered_articles[0].get('interest_score', 0)}/10 до {filtered_articles[-1].get('interest_score', 0)}/10)" if filtered_articles else "")

    return filtered_articles


def get_all_articles_with_filter_results(articles: List[Dict[str, str]],
                                        flow_id: str,
                                        flowise_host: str) -> List[Dict[str, str]]:
    """
    Возвращает все статьи с результатами фильтрации (включая отклоненные).

    Args:
        articles: Исходные статьи
        flow_id: ID потока Flowise
        flowise_host: Хост Flowise

    Returns:
        List[Dict]: Все статьи с информацией о фильтрации
    """
    articles_with_results = []

    for article in articles:
        relevance_check = check_relevance_with_flowise(article, flow_id, flowise_host)

        article_with_meta = article.copy()
        article_with_meta['filter_result'] = relevance_check

        # Используем данные от фильтра, если они есть
        if relevance_check['title_ru']:
            article_with_meta['title_filtered'] = relevance_check['title_ru']
        if relevance_check['summary']:
            article_with_meta['summary_filtered'] = relevance_check['summary']

        article_with_meta['content_type'] = relevance_check['content_type']
        article_with_meta['interest_score'] = relevance_check['interest_score']

        articles_with_results.append(article_with_meta)

        if relevance_check['is_relevant']:
            logger.debug(f"✓ Статья прошла фильтр: {article['title'][:50]}... (Оценка: {relevance_check['interest_score']}/10)")
        else:
            logger.debug(f"✗ Статья отклонена: {article['title'][:50]}... Причина: {relevance_check['relevance_reason']}")

    return articles_with_results