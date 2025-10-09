"""
Базовый класс для всех агентов.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from django.utils import timezone


class BaseAgent(ABC):
    """Базовый класс для всех агентов пайплайна."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.started_at = None
        self.finished_at = None
        self.error_message = None
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Основной метод обработки данных.
        
        Args:
            data: Входные данные для обработки
            
        Returns:
            Результат обработки
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Проверка конфигурации агента.
        
        Returns:
            bool: True если конфигурация корректна
        """
        return True
    
    def run(self, data: Any) -> Any:
        """
        Запускает агента с обработкой ошибок.
        
        Args:
            data: Входные данные
            
        Returns:
            Результат обработки или None при ошибке
        """
        self.started_at = timezone.now()
        
        try:
            # Проверяем конфигурацию
            if not self.validate_config():
                raise ValueError("Некорректная конфигурация агента")
            
            # Выполняем обработку
            result = self.process(data)
            self.finished_at = timezone.now()
            return result
            
        except Exception as e:
            self.finished_at = timezone.now()
            self.error_message = str(e)
            raise
    
    def get_execution_time(self) -> float:
        """
        Возвращает время выполнения в секундах.
        
        Returns:
            float: Время выполнения в секундах
        """
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """
        Возвращает статус агента.
        
        Returns:
            Dict: Статус агента
        """
        return {
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'execution_time': self.get_execution_time(),
            'error_message': self.error_message,
            'has_error': bool(self.error_message)
        }
