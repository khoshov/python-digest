import requests
import json
from typing import Dict

from logger.logger import setup_logger

logger = setup_logger(module_name=__name__)


class CopywriterService:
    def __init__(self):
        pass

    def call_flowise_copywriter(self, flow_id: str, article: Dict[str, str], flowise_host: str) -> Dict[str, str]:
        """
        Вызывает Flowise API для создания Telegram-поста из новости.
        
        Новый формат ответа содержит:
        - post: готовый текст для Telegram с Markdown
        - image_idea: идея для сопроводительного изображения
        
        Args:
            flow_id: ID Flowise потока для копирайтинга
            article: Словарь с данными статьи (title, summary, url)
            flowise_host: Хост Flowise API
            
        Returns:
            Dict: {"post": "текст поста", "image_idea": "описание картинки"}
        """
        url = f"{flowise_host}/api/v1/prediction/{flow_id}"

        payload = {
            "question": f"Заголовок: {article['title']}, Краткое содержание: {article['summary']}, Ссылка: {article['url']}",
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result_text = response.json().get("text", "").strip()
            
            # Пытаемся парсить структурированный ответ
            try:
                # Ищем JSON в ответе
                if "post:" in result_text and "image_idea:" in result_text:
                    lines = result_text.split('\n')
                    post_content = ""
                    image_idea = ""
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith("post:"):
                            current_section = "post"
                            post_content = line.replace("post:", "").strip()
                        elif line.startswith("image_idea:"):
                            current_section = "image_idea"
                            image_idea = line.replace("image_idea:", "").strip()
                        elif current_section == "post" and line:
                            post_content += "\n" + line
                        elif current_section == "image_idea" and line:
                            image_idea += " " + line
                    
                    return {
                        "post": post_content.strip(),
                        "image_idea": image_idea.strip()
                    }

                logger.warning(result_text)
                # Если структуры нет, возвращаем весь текст как пост
                logger.warning("Копирайтер вернул ответ не в ожидаемом формате")
                return {
                    "post": result_text,
                    "image_idea": "Абстрактная иллюстрация на тему Python разработки"
                }
                
            except Exception as e:
                logger.error(f"Ошибка парсинга ответа копирайтера: {e}")
                return {
                    "post": result_text,
                    "image_idea": "Изображение на тему Python"
                }
                
        except Exception as e:
            logger.error(f"Ошибка при вызове Flowise copywriter: {e}")
            return {
                "post": f"Ошибка создания поста для: {article['title']}",
                "image_idea": "Ошибка"
            }
