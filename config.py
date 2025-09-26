"""
Конфигурация для SMM Agents Pipeline.
"""

import os
from typing import List
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


@dataclass
class Settings:
    """Настройки приложения."""

    # Flowise настройки
    flowise_host: str = os.getenv("FLOWISE_HOST", "")
    flowise_filter_id: str = os.getenv("FLOWISE_FILTER_ID", "")
    flowise_copywriter_id: str = os.getenv("FLOWISE_COPYWRITER_ID", "")

    # Google API настройки
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")
    enable_google_news: bool = os.getenv("ENABLE_GOOGLE_NEWS", "false").lower() == "true"

    # RSS настройки
    enable_rss_news: bool = os.getenv("ENABLE_RSS_NEWS", "true").lower() == "true"
    rss_hours_period: int = int(os.getenv("RSS_HOURS_PERIOD", "168"))  # 7 дней по ТЗ

    # OpenAI настройки
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    generate_images: bool = os.getenv("GENERATE_IMAGES", "false").lower() == "true"

    # Email настройки
    smtp_server: str = os.getenv("SMTP_SERVER", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Получатели email (разделенные запятыми)
    email_recipients: List[str] = None
    email_from: str = os.getenv("EMAIL_FROM", "")
    email_subject: str = os.getenv("EMAIL_SUBJECT", "Python Digest - Еженедельный дайджест")
    enable_email_sending: bool = os.getenv("ENABLE_EMAIL_SENDING", "false").lower() == "true"

    def __post_init__(self):
        """Дополнительная обработка после инициализации."""
        # Обработка списка получателей email
        recipients_str = os.getenv("EMAIL_RECIPIENTS", "")
        if recipients_str:
            self.email_recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
        else:
            self.email_recipients = []


# Глобальный экземпляр настроек
settings = Settings()