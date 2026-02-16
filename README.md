# AI Assistant - RAG система рекомендаций

Интеллектуальная система для поиска и рекомендаций статей на основе **Retrieval-Augmented Generation (RAG)** с поддержкой русского языка.

## Возможности

- **Умный поиск** по базе статей с multilingual эмбеддингами
- **Генерация ответов** на основе контекста с помощью LLM (Qwen 2.5)
- **Переранжирование** результатов для максимальной релевантности
- **Поддержка русского языка** и других языков
- **Многопользовательская система** с JWT-авторизацией
- **История чата** для каждого пользователя с возможностью очистки
- **Аналитика и статистика** использования в реальном времени
- **Админ-панель** для управления статьями, пользователями и тегами
- **Загрузка документов** (PDF, DOCX, Markdown) с автоматическим парсингом

## Быстрый старт

### Предварительные требования

- Python 3.8+
- [Ollama](https://ollama.ai/) для LLM

### Установка

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Установите и запустите Ollama с LLM моделью:**
   ```bash
   ollama pull qwen2.5:7b
   ollama serve
   ```

3. **Переиндексируйте статьи:**
   ```bash
   python reindex_articles.py
   ```

4. **Запустите сервер:**
   ```bash
   python main.py
   ```

5. **Откройте приложение:**
   - Чат: http://localhost:8000/chat
   - Админ-панель: http://localhost:8000/admin
   - API документация: http://localhost:8000/docs

### Авторизация по умолчанию

- **Логин:** admin
- **Пароль:** admin

**Важно:** Смените пароль после первого входа!

## Архитектура

### RAG Pipeline

```
1. Chunking    -> Разбиение документов на чанки (800 символов, перекрытие 100)
2. Embedding   -> Векторизация с multilingual моделью (paraphrase-multilingual-MiniLM-L12-v2)
3. Retrieval   -> Поиск релевантных чанков в ChromaDB (top-30)
4. Reranking   -> Переранжирование с cross-encoder (top-5)
5. Generation  -> Генерация ответа с LLM (Qwen 2.5:7b через Ollama)
```

### Технологический стек

**Backend:**
- FastAPI + Uvicorn (асинхронный веб-сервер)
- SQLite (реляционная БД для пользователей, статей, сессий)
- ChromaDB (векторное хранилище)
- JWT (авторизация через python-jose)
- Argon2 (хеширование паролей)

**RAG/ML:**
- Sentence-Transformers (embeddings и cross-encoder)
- PyTorch (inference)
- LangChain (text splitter для чанкинга)
- Ollama (локальный LLM)

**Frontend:**
- Vanilla JavaScript (без фреймворков)
- Bootstrap 5.3.0 + Bootstrap Icons (UI)
- Chart.js 4.4.0 (графики в админ-панели)

## Структура проекта

```
.
├── api/                    # FastAPI приложение
│   ├── app.py              # Endpoints и RecommendationAPI
│   └── schemas.py          # Pydantic схемы
├── auth/                   # Система авторизации
│   └── user_db.py          # Управление пользователями (Argon2)
├── config/                 # Конфигурация
│   └── settings.py         # Настройки API, пути к БД
├── database/               # Работа с БД
│   ├── db_init.py          # Инициализация SQLite, создание таблиц
│   ├── article_db.py       # CRUD для статей
│   ├── session_manager.py  # Сессии, история чата, аналитика
│   ├── tag_manager.py      # Управление тегами
│   └── excel_loader.py     # Загрузка из Excel
├── data/                   # Данные приложения
│   ├── app.db              # SQLite база данных
│   ├── articles.xlsx       # Excel со статьями
│   └── chroma_db/          # ChromaDB векторное хранилище
├── frontend/               # Веб-интерфейс
│   ├── chat.html           # Чат с авторизацией и историей
│   ├── admin.html          # Админ-панель
│   └── favicon.svg         # Иконка
├── rag/                    # RAG Pipeline
│   ├── rag_pipeline.py     # Главный pipeline
│   ├── chunker.py          # Разбиение текста на чанки
│   ├── vector_store.py     # ChromaDB интеграция
│   ├── reranker.py         # Cross-encoder переранжирование
│   └── llm_generator.py    # Интеграция с Ollama
├── scripts/                # Утилиты
│   └── migrate_to_sqlite.py
├── utils/                  # Вспомогательные модули
│   └── document_parsers.py # Парсеры PDF, DOCX, Markdown
├── main.py                 # Точка входа
├── security.py             # JWT токены и аутентификация
├── reindex_articles.py     # Скрипт переиндексации
├── generate_articles.py    # Генератор тестовых статей
├── test_rag.py             # Тесты RAG pipeline
├── test_system.py          # Интеграционные тесты
└── requirements.txt        # Python зависимости
```

## База данных (SQLite)

### Таблицы

| Таблица | Назначение |
|---------|-----------|
| `users` | Пользователи (username, hashed_password, role, is_active) |
| `articles` | Статьи для RAG (title, content, url, tags) |
| `sessions` | Сессии пользователей (total_reward, interaction_count) |
| `interactions` | Все взаимодействия (user_query, article_id, reward) |
| `chat_clear_history` | Метка времени очистки чата пользователем |

Таблица `chat_clear_history` используется для soft-delete: при очистке истории чата данные **не удаляются** из `interactions`, а скрываются от пользователя. Вся аналитика и статистика в админ-панели продолжает работать с полными данными.

## API Endpoints

### Авторизация
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/login` | Авторизация (возвращает JWT-токен) |
| POST | `/register` | Регистрация нового пользователя |
| GET | `/verify` | Проверка валидности токена |

### Чат и история
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/ask` | Задать вопрос (RAG pipeline) |
| GET | `/chat/history` | Получить историю чата пользователя |
| DELETE | `/chat/history` | Очистить историю чата (soft-delete) |

### Статьи и данные
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/articles` | Список всех статей |
| GET | `/session/{user_id}` | Статистика сессии пользователя |
| GET | `/users` | Список пользователей (имена) |
| GET | `/health` | Проверка работоспособности |

### Админ-панель (требует роль admin)
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/admin/articles` | Список статей (пагинация, фильтрация) |
| POST | `/admin/articles` | Создать статью |
| PUT | `/admin/articles/{id}` | Обновить статью |
| DELETE | `/admin/articles/{id}` | Удалить статью |
| POST | `/admin/upload` | Загрузка документа (PDF, DOCX, MD) |
| POST | `/admin/rag/reindex` | Переиндексация статей |
| GET | `/admin/rag/stats` | Статистика RAG |
| GET | `/admin/users` | Список пользователей (подробно) |
| POST | `/admin/users` | Создать пользователя |
| DELETE | `/admin/users/{username}` | Удалить пользователя |
| PUT | `/admin/users/{username}/role` | Изменить роль |
| PUT | `/admin/users/{username}/password` | Изменить пароль |
| GET | `/admin/tags` | Список тегов |
| DELETE | `/admin/tags/{tag}` | Удалить тег |
| PUT | `/admin/tags/{tag}` | Переименовать тег |
| GET | `/admin/analytics/overview` | Общая аналитика |
| GET | `/admin/analytics/timeline` | Аналитика по времени |

## Настройка RAG

Основные параметры настраиваются в `main.py`:

```python
RAGPipeline(
    chunk_size=800,
    chunk_overlap=100,
    embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
    reranker_model="mmarco-mMiniLMv2-L12-H384-v1",
    llm_model="qwen2.5:7b",
    llm_base_url="http://localhost:11434",
    retrieval_top_k=30,
    rerank_top_k=5
)
```

## Основные команды

```bash
# Запуск сервера
python main.py

# Переиндексация статей
python reindex_articles.py

# Генерация тестовых статей
python generate_articles.py

# Тестирование RAG pipeline
python test_rag.py

# Интеграционное тестирование
python test_system.py

# Проверка работоспособности
curl http://localhost:8000/health
```

## Устранение проблем

### "Cannot connect to Ollama"
```bash
ollama serve
```

### "Model not found"
```bash
ollama pull qwen2.5:7b
```

### Низкое качество ответов
```bash
python reindex_articles.py
```

## Лицензия

Proprietary - Все права защищены
