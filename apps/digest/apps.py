"""
Конфигурация приложения digest.
"""

from django.apps import AppConfig


class DigestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.digest"
    verbose_name = "Дайджест контента"

    def ready(self):
        """
        Инициализация приложения.
        Здесь можно добавить сигналы или другие инициализации.
        """
        try:
            from . import signals
        except ImportError:
            pass
