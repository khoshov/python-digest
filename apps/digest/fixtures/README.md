# Фикстуры для Python Digest

Этот файл содержит начальные данные для проекта Python Digest на основе технического задания.

## Что включено:

### Проект
- **Python Digest Weekly** - активный проект с настройками:
  - Период RSS: 168 часов (7 дней)
  - Максимум статей с источника: 20
  - Финальных постов: 8
  - RSS и Google CSE включены

### RSS Источники (12 штук)

**Приоритет 1 (самые важные):**
1. **Habr - Python** - `https://habr.com/ru/rss/hub/python/all/`
2. **Real Python** - `https://realpython.com/atom.xml`
3. **Python.org Official Blog** - `https://www.python.org/feeds/python.rss/`
4. **Python Weekly** - новостная рассылка

**Приоритет 2 (важные):**
5. **Planet Python** - агрегатор Python блогов
6. **Python Software Foundation Blog** - официальный блог PSF
7. **Python Library - Blog** - блог о Python библиотеках
8. **Tproger - Python** - русскоязычный портал
9. **PyPI Blog** - новости о Python Package Index

**Приоритет 3 (дополнительные):**
10. **GitHub Blog - Python** - статьи о Python на GitHub
11. **Hynek Schlawack's Blog** - блог известного Python-разработчика
12. **Full Stack Python** - материалы о разработке на Python

### Ключевые слова для Google CSE (30 штук)

**Приоритет 1 (основные):**
- Python
- Django
- FastAPI
- Python 3.13

**Приоритет 2 (фреймворки и инструменты):**
- Flask
- asyncio
- Pandas
- NumPy
- Machine Learning Python
- Data Science Python
- SQLAlchemy
- Pydantic
- Python async
- Python REST API
- Python tutorial
- Python ORM

**Приоритет 3 (специализированные):**
- Pytest
- Poetry Python
- Python performance
- Python best practices
- Python typing
- Python web scraping
- Celery Python
- Python Docker
- Python microservices
- Python GraphQL
- Python course
- Python developer career
- Python security

**Приоритет 4 (развлекательный контент):**
- Python meme

## Загрузка фикстур

### Свежая установка (с пустой БД):

```bash
# 1. Создать миграции
python manage.py makemigrations

# 2. Применить миграции
python manage.py migrate

# 3. Загрузить фикстуры
python manage.py loaddata apps/digest/fixtures/python_digest_initial.json
```

### Обновление существующей БД:

```bash
# Загрузить фикстуры (обновит существующие записи по ID)
python manage.py loaddata apps/digest/fixtures/python_digest_initial.json
```

### Проверка загруженных данных:

```bash
# Список проектов
python manage.py run_digest --list-projects

# Должен показать:
# 📋 Список проектов:
#   [1] Python Digest Weekly - ✅ АКТИВНЫЙ
```

## Соответствие ТЗ

### ✅ Форматы контента (из ТЗ):
1. **Новости из мира Python** - покрыто RSS и ключевыми словами
2. **Технические статьи** - Real Python, Habr, Hynek.me
3. **Статьи о развитии инженеров** - "Python developer career", "Python best practices"
4. **Мемы и истории** - ключевое слово "Python meme"

### ✅ Источники (из ТЗ):
- ✅ habr.com - `https://habr.com/ru/rss/hub/python/all/`
- ✅ tproger.ru - `https://tproger.ru/tag/python/feed/`
- ✅ realpython.com - `https://realpython.com/atom.xml`
- ✅ planetpython.org - `https://planetpython.org/rss20.xml`
- ✅ hynek.me - `https://hynek.me/articles/feed/`
- ✅ pyfound.blogspot.com - `https://pyfound.blogspot.com/feeds/posts/default`
- ✅ blog.pythonlibrary.org - `https://www.blog.pythonlibrary.org/feed/`
- ✅ github.blog - `https://github.blog/tag/python/feed/`

**Дополнительно добавлены:**
- python.org/feeds - официальный блог Python
- Python Weekly - популярная рассылка
- Full Stack Python - обучающий ресурс
- PyPI Blog - новости о пакетах

### ✅ Требования к контенту:
- **Дата публикации**: до 7 дней (168 часов) ✅ настроено в проекте
- **Целевая аудитория**: практикующие разработчики + начинающие ✅
- **Количество постов**: 8 ✅ настроено в `max_final_posts`

### ✅ Формат поста (обрабатывается промптами):
- Заголовок: макс 100 символов, русский язык ✅
- Тип материала: новость/статья/видео/история/мем ✅
- Анонс: макс 350 символов, русский язык ✅
- Ссылка ✅

## Расширение данных

Вы можете добавить дополнительные источники и ключевые слова:

### Через админку Django:
1. Перейдите в `/admin/`
2. Откройте "RSS источники" или "Ключевые слова (Google CSE)"
3. Добавьте новые записи

### Через новые фикстуры:
1. Отредактируйте `python_digest_initial.json`
2. Перезагрузите: `python manage.py loaddata apps/digest/fixtures/python_digest_initial.json`

## Примечания

- Все RSS URL проверены и являются валидными фидами
- Ключевые слова покрывают все популярные Python-технологии
- Приоритеты настроены для баланса между новостями и техническим контентом
- Можно отключить неактуальные источники через поле `is_active`
