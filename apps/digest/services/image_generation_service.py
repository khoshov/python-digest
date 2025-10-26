import base64
from pathlib import Path
from typing import Optional

import requests

from logger.logger import setup_logger

logger = setup_logger(module_name=__name__)


class ImageGenerationService:
    """
    Модуль для генерации изображений по текстовому описанию.
    Класс для генерации изображений через OpenAI DALL-E API.
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Инициализация генератора изображений.

        Args:
            api_key: OpenAI API key
            **kwargs: Дополнительные параметры для генерации
        """
        self.api_key = api_key
        self.config = kwargs
        self.output_dir = Path("generated_images")
        self.output_dir.mkdir(exist_ok=True)

    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Генерация изображения через OpenAI DALL-E API.

        Args:
            prompt: Текстовое описание изображения
            **kwargs: Дополнительные параметры (size, quality, style)

        Returns:
            str: Путь к сохраненному изображению или None при ошибке
        """
        if not self.api_key:
            logger.error("OpenAI API key не настроен")
            return None

        url = "https://api.openai.com/v1/images/generations"

        payload = {
            "model": kwargs.get("model", "dall-e-3"),
            "prompt": prompt,
            "size": kwargs.get("size", "1024x1024"),
            "quality": kwargs.get("quality", "standard"),
            "style": kwargs.get("style", "natural"),
            "n": 1,
            "response_format": "b64_json",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            logger.debug(f"Генерируем изображение через OpenAI: {prompt[:50]}...")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            result = response.json()
            image_data = base64.b64decode(result["data"][0]["b64_json"])

            # Сохраняем изображение
            filename = f"openai_{hash(prompt) % 1000000}.png"
            filepath = self.output_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.debug(f"✅ Изображение сохранено: {filepath}")
            return str(filepath)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка OpenAI API: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return None


def generate_image_for_post(image_idea: str, api_key: str, **kwargs) -> Optional[str]:
    """
    Упрощенная функция для генерации изображения к посту.

    Args:
        image_idea: Описание изображения от копирайтера
        api_key: OpenAI API key
        **kwargs: Дополнительные параметры для генерации

    Returns:
        str: Путь к изображению или None при ошибке
    """
    enhanced_prompt = f"Professional, high-quality illustration for social media post about AI and technology. {image_idea}. Modern style, clean design, suitable for Telegram post."

    generator = ImageGenerationService(api_key=api_key, **kwargs)
    return generator.generate_image(enhanced_prompt, **kwargs)
