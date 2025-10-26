# 🤖 Python Digest - SMM Agents Pipeline

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![UV](https://img.shields.io/badge/UV-Package%20Manager-orange.svg)](https://astral.sh)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Программа для обработки новостей и генерации контента для социальных сетей с использованием современных инструментов Python.

## 🚀 Быстрый старт

### Предварительные требования
- **Python 3.12+**
- **UV** (современный менеджер пакетов Python)
- **Docker** (опционально, для контейнеризации)

### Установка UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Локальная установка
```bash
# Клонирование репозитория
git clone <repository-url>
cd python-digest

# Установка зависимостей с UV
uv sync

# Настройка окружения
cp .env.example .env
# Отредактируйте .env файл, установите необходимые переменные

# Запуск Django приложения
uv run manage.py migrate
uv run manage.py runserver
```

### Запуск пайплайна
```bash
# Основной пайплайн обработки
uv run python main.py

# Или запуск отдельных сервисов
uv run python -m agents.digest_service
uv run python -m agents.scout_service
```

## 🏗️ Архитектура проекта

Проект построен на модульной архитектуре с использованием Django и специализированных агентов:

### Основные сервисы
- **✅ digest_service.py** - основной пайплайн обработки
- **✅ scout_service.py** - сбор новостей из RSS-фидов
- **✅ filter_service.py** - фильтрация и классификация контента
- **✅ copywriter_service.py** - создание постов для соцсетей
- **✅ image_generation_service.py** - генерация изображений
- **✅ deduplication_service.py** - удаление дубликатов
- **✅ email_service.py** - отправка email уведомлений
- **✅ configuration_service.py** - работа с конфигурацией

### Структура проекта
```
python-digest/
├── 📦 pyproject.toml          # Конфигурация проекта и зависимости
├── 📦 uv.lock                 # Файл блокировки зависимостей
├── 📝 .env.example            # Пример переменных окружения
├── 🔒 .gitignore              # Игнорируемые файлы
│
├── agents/                    # Сервисы пайплайна
│   ├── digest_service.py      # Основной пайплайн
│   ├── scout_service.py       # Сбор новостей
│   ├── filter_service.py      # Фильтрация
│   ├── copywriter_service.py  # Создание постов
│   ├── image_generation_service.py  # Генерация изображений
│   ├── deduplication_service.py     # Удаление дубликатов
│   ├── email_service.py       # Отправка email
│   └── configuration_service.py     # Конфигурация
│
├── apps/
│   └── digest/                # Django приложение
│       ├── admin.py           # Админ-панель
│       ├── models.py          # Модели данных
│       ├── views.py           # Представления
│       ├── urls.py            # URL конфигурация
│       └── tests.py           # Тесты
│
├── config/                    # Настройки Django
│   ├── settings.py            # Основные настройки
│   ├── urls.py                # URL конфигурация
│   ├── asgi.py                # ASGI приложение
│   └── wsgi.py                # WSGI приложение
│
├── logger/                    # Логирование
│   └── logger.py              # Конфигурация логгера
│
├── main.py                    # Основной скрипт
├── manage.py                  # Django management
└── config.py                  # Конфигурация приложения
```

## 🛠️ Команды разработки

### Основные команды
```bash
# Запуск Django сервера
uv run manage.py runserver

# Миграции базы данных
uv run manage.py migrate
uv run manage.py makemigrations

# Создание суперпользователя
uv run manage.py createsuperuser

# Запуск тестов
uv run manage.py test
```

### Управление зависимостями с UV
```bash
uv sync                        # Синхронизировать зависимости
uv add package                 # Добавить пакет
uv remove package              # Удалить пакет
uv run command                 # Запустить команду в окружении
uv python install 3.12         # Установить Python 3.12
```

### Запуск отдельных сервисов
```bash
# Сбор новостей
uv run python -m agents.scout_service

# Фильтрация контента
uv run python -m agents.filter_service

# Генерация постов
uv run python -m agents.copywriter_service

# Генерация изображений
uv run python -m agents.image_generation_service
```

## 🔧 Конфигурация

### Переменные окружения
Скопируйте `.env.example` в `.env` и настройте необходимые параметры:

```bash
# Базовые настройки Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Настройки базы данных (SQLite по умолчанию)
DATABASE_URL=sqlite:///db.sqlite3

# Настройки для сбора новостей
RSS_FEEDS=https://example.com/feed1,https://example.com/feed2
NEWS_API_KEY=your-news-api-key

# Настройки для социальных сетей
TWITTER_API_KEY=your-twitter-key
FACEBOOK_ACCESS_TOKEN=your-facebook-token

# Настройки email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 📊 Функциональность

### Основные возможности
- **Автоматический сбор новостей** из RSS-фидов и API
- **Интеллектуальная фильтрация** контента по релевантности
- **Генерация креативного контента** для социальных сетей
- **Создание изображений** для визуального контента
- **Удаление дубликатов** и контроль качества
- **Email уведомления** о результатах работы
- **Веб-интерфейс** для управления через Django Admin

### Модели данных
Проект включает следующие основные модели:
- Новостные статьи и источники
- Категории и теги для классификации
- Сгенерированный контент для соцсетей
- Статистика и метрики эффективности

## 🐳 Docker поддержка

### Сборка и запуск
```bash
# Сборка образа
docker build -t python-digest .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env python-digest
```

### Docker Compose (для разработки)
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
```

## 🔍 Качество кода

Проект использует современные инструменты для обеспечения качества кода:

### Форматирование и линтинг
```bash
# Установка инструментов качества
uv add --dev ruff black mypy

# Проверка кода
uvx ruff check .
uvx black --check .
uvx mypy .

# Автоматическое исправление
uvx ruff check --fix .
uvx black .
```

### Pre-commit хуки
```bash
# Установка pre-commit
uv add --dev pre-commit

# Установка хуков
pre-commit install

# Запуск вручную
pre-commit run --all-files
```

## 🚀 Деплой

### Продакшен настройки
```bash
# В .env файле для продакшена
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Мониторинг здоровья
```bash
# Проверка состояния приложения
curl http://localhost:8000/health/
```

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для функции: `git checkout -b feature/amazing-feature`
3. Зафиксируйте изменения: `git commit -m 'Add amazing feature'`
4. Отправьте в ветку: `git push origin feature/amazing-feature`
5. Создайте Pull Request

### Правила разработки
- Используйте современные инструменты Python (UV, Ruff)
- Следуйте PEP 8 стандартам
- Добавляйте тесты для новой функциональности
- Обновляйте документацию

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте документацию в файле `CLAUDE.md`
2. Создайте Issue с подробным описанием проблемы
3. Используйте логи для диагностики: `tail -f logs/app.log`

---

**Разработано с ❤️ используя современные инструменты Python и модульную архитектуру**

### 🔗 Полезные ссылки

- [Django Documentation](https://docs.djangoproject.com/)
- [UV Documentation](https://docs.astral.sh/uv/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Docker Documentation](https://docs.docker.com/)
- [Python 3.12 Documentation](https://docs.python.org/3.12/)
