from typing import List, Dict
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from logger.logger import setup_logger
from apps.digest import prompts

logger = setup_logger(module_name=__name__)


# Pydantic модель для структурированного ответа фильтра
class FilterResponse(BaseModel):
    is_relevant: bool = Field(description="Релевантна ли статья для Python Digest")
    relevance_reason: str = Field(description="Причина релевантности или нерелевантности")
    interest_score: float = Field(description="Оценка интереса от 0 до 10", ge=0, le=10)
    interest_reason: str = Field(description="Почему такая оценка интереса")
    content_type: str = Field(description="Тип контента: tutorial/news/library/event/opinion/meme/other")
    summary: str = Field(description="Краткое описание на русском (до 350 символов)", max_length=350)
    title_ru: str = Field(description="Заголовок на русском (до 100 символов)", max_length=100)
    url: str = Field(description="URL статьи")


class FilterService:
    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=FilterResponse)

    def check_relevance_with_deepseek(
        self,
        article: Dict[str, str],
        deepseek_api_key: str,
        system_prompt: str = None,
        user_prompt: str = None
    ) -> Dict[str, any]:
        """
        Проверяет релевантность статьи через DeepSeek API используя LangChain.

        Args:
            article: Словарь с данными статьи (title, summary, url)
            deepseek_api_key: API ключ DeepSeek
            system_prompt: Системный промпт (опционально)
            user_prompt: Пользовательский промпт (опционально)

        Returns:
            Dict: Результаты фильтрации
        """
        try:
            # Создаем LLM модель DeepSeek через OpenAI-совместимый API
            llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                temperature=0.3,
            )

            # Используем промпты по умолчанию, если не переданы
            if system_prompt is None:
                system_prompt = prompts.FILTER_SYSTEM_PROMPT

            if user_prompt is None:
                user_prompt = prompts.FILTER_USER_PROMPT

            # Создаем prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])

            # Создаем цепочку
            chain = prompt | llm | self.parser

            # Вызываем цепочку
            result = chain.invoke({
                "title": article.get('title', ''),
                "summary": article.get('summary', ''),
                "url": article.get('url', ''),
                "format_instructions": self.parser.get_format_instructions()
            })

            # Логируем результат для отладки
            logger.debug(
                f"📥 Ответ от DeepSeek для '{article.get('title', '')[:50]}...': релевантность={result.get('is_relevant')}, оценка={result.get('interest_score')}/10"
            )

            return result

        except Exception as e:
            logger.error(f"Ошибка при проверке релевантности через DeepSeek: {e}")
            return {
                "is_relevant": False,
                "relevance_reason": f"Ошибка API: {str(e)[:100]}",
                "interest_score": 0,
                "interest_reason": "Ошибка API",
                "content_type": "Ошибка",
                "summary": "",
                "title_ru": "",
                "url": article.get("url", ""),
            }

    def filter_news(
        self,
        articles: List[Dict[str, str]],
        deepseek_api_key: str,
        system_prompt: str = None,
        user_prompt: str = None
    ) -> List[Dict[str, str]]:
        """
        Фильтрует статьи через DeepSeek API.

        Args:
            articles: Список статей для фильтрации
            deepseek_api_key: API ключ DeepSeek
            system_prompt: Системный промпт (опционально)
            user_prompt: Пользовательский промпт (опционально)

        Returns:
            List[Dict]: Отфильтрованные статьи
        """
        filtered_articles = []

        for article in articles:
            relevance_check = self.check_relevance_with_deepseek(
                article, deepseek_api_key, system_prompt, user_prompt
            )

            # Добавляем информацию о фильтрации к статье
            article_with_meta = article.copy()
            article_with_meta["filter_result"] = relevance_check

            if relevance_check["is_relevant"]:
                # Используем данные от фильтра, если они есть
                if relevance_check["title_ru"]:
                    article_with_meta["title"] = relevance_check["title_ru"]
                if relevance_check["summary"]:
                    article_with_meta["summary"] = relevance_check["summary"]

                # Добавляем все данные фильтрации
                article_with_meta["content_type"] = relevance_check["content_type"]
                article_with_meta["interest_score"] = relevance_check["interest_score"]
                article_with_meta["is_relevant"] = True
                article_with_meta["relevance_reason"] = relevance_check["relevance_reason"]
                article_with_meta["interest_reason"] = relevance_check["interest_reason"]

                filtered_articles.append(article_with_meta)
                logger.debug(
                    f"✓ Статья прошла фильтр: {article['title'][:50]}... (Оценка: {relevance_check['interest_score']}/10, Тип: {relevance_check['content_type']})"
                )
            else:
                logger.debug(
                    f"✗ Статья отклонена: {article['title'][:50]}... Причина: {relevance_check['relevance_reason']}"
                )

        # Сортируем по оценке интереса (от высокой к низкой)
        filtered_articles.sort(key=lambda x: x.get("interest_score", 0), reverse=True)

        logger.info(
            f"📊 Отфильтрованные статьи отсортированы по интересности (от {filtered_articles[0].get('interest_score', 0)}/10 до {filtered_articles[-1].get('interest_score', 0)}/10)"
            if filtered_articles
            else ""
        )

        return filtered_articles

    def get_all_articles_with_filter_results(
        self,
        articles: List[Dict[str, str]],
        deepseek_api_key: str,
        system_prompt: str = None,
        user_prompt: str = None
    ) -> List[Dict[str, str]]:
        """
        Возвращает все статьи с результатами фильтрации (включая отклоненные).

        Args:
            articles: Исходные статьи
            deepseek_api_key: API ключ DeepSeek
            system_prompt: Системный промпт (опционально)
            user_prompt: Пользовательский промпт (опционально)

        Returns:
            List[Dict]: Все статьи с информацией о фильтрации
        """
        articles_with_results = []

        for article in articles:
            relevance_check = self.check_relevance_with_deepseek(
                article, deepseek_api_key, system_prompt, user_prompt
            )

            article_with_meta = article.copy()
            article_with_meta["filter_result"] = relevance_check

            # Используем данные от фильтра, если они есть
            if relevance_check["title_ru"]:
                article_with_meta["title_filtered"] = relevance_check["title_ru"]
            if relevance_check["summary"]:
                article_with_meta["summary_filtered"] = relevance_check["summary"]

            # Добавляем все данные фильтрации для сохранения в БД
            article_with_meta["content_type"] = relevance_check["content_type"]
            article_with_meta["interest_score"] = relevance_check["interest_score"]
            article_with_meta["is_relevant"] = relevance_check["is_relevant"]
            article_with_meta["relevance_reason"] = relevance_check["relevance_reason"]
            article_with_meta["interest_reason"] = relevance_check["interest_reason"]

            articles_with_results.append(article_with_meta)

            if relevance_check["is_relevant"]:
                logger.debug(
                    f"✓ Статья прошла фильтр: {article['title'][:50]}... (Оценка: {relevance_check['interest_score']}/10)"
                )
            else:
                logger.debug(
                    f"✗ Статья отклонена: {article['title'][:50]}... Причина: {relevance_check['relevance_reason']}"
                )

        return articles_with_results
