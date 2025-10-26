from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from logger.logger import setup_logger
from apps.digest import prompts

logger = setup_logger(module_name=__name__)


# Pydantic модель для структурированного ответа копирайтера
class CopywriterResponse(BaseModel):
    post: str = Field(description="Текст поста для Telegram с Markdown форматированием (до 500 символов)", max_length=500)
    image_idea: str = Field(description="Идея для сопроводительного изображения на английском языке для DALL-E")


class CopywriterService:
    def __init__(self):
        self.parser = JsonOutputParser(pydantic_object=CopywriterResponse)

    def call_deepseek_copywriter(
        self,
        article: Dict[str, str],
        deepseek_api_key: str,
        system_prompt: str = None,
        user_prompt: str = None
    ) -> Dict[str, str]:
        """
        Вызывает DeepSeek API для создания Telegram-поста из новости используя LangChain.

        Новый формат ответа содержит:
        - post: готовый текст для Telegram с Markdown
        - image_idea: идея для сопроводительного изображения

        Args:
            article: Словарь с данными статьи (title, summary, url)
            deepseek_api_key: API ключ DeepSeek
            system_prompt: Системный промпт (опционально)
            user_prompt: Пользовательский промпт (опционально)

        Returns:
            Dict: {"post": "текст поста", "image_idea": "описание картинки"}
        """
        try:
            # Создаем LLM модель DeepSeek через OpenAI-совместимый API
            llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
                temperature=0.7,
            )

            # Используем промпты по умолчанию, если не переданы
            if system_prompt is None:
                system_prompt = prompts.COPYWRITER_SYSTEM_PROMPT

            if user_prompt is None:
                user_prompt = prompts.COPYWRITER_USER_PROMPT

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
            logger.debug(f"📝 Создан пост для '{article.get('title', '')[:50]}...' ({len(result.get('post', ''))} символов)")

            return result

        except Exception as e:
            logger.error(f"Ошибка при вызове DeepSeek copywriter: {e}")
            return {
                "post": f"Ошибка создания поста для: {article.get('title', 'неизвестная статья')}",
                "image_idea": "Error generating image idea",
            }
