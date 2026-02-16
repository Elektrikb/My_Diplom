# 🤖 AI Assistant - RAG система рекомендаций

Интеллектуальная система для поиска и рекомендаций статей на основе **Retrieval-Augmented Generation (RAG)** с отличной поддержкой русского языка.

## ✨ Возможности

- 🔍 **Умный поиск** по базе статей с multilingual эмбеддингами
- 🤖 **Генерация ответов** на основе контекста с помощью LLM (Qwen 2.5)
- 📊 **Переранжирование** результатов для максимальной релевантности
- 🌍 **Отличная поддержка русского языка** и других языков
- 👥 **Многопользовательская система** с авторизацией
- 📈 **Аналитика и статистика** использования
- ⚙️ **Админ-панель** для управления статьями и пользователями

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- [Ollama](https://ollama.ai/) для LLM
- ChromaDB для векторного хранилища

### Установка

1. **Клонируйте репозиторий** (если еще не сделано)

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Установите LLM модель:**
   ```bash
   ollama pull qwen2.5:7b
   ```

4. **Запустите переиндексацию статей:**
   ```bash
   python reindex_articles.py
   ```

5. **Запустите сервер:**
   ```bash
   python main.py
   ```

6. **Откройте приложение:**
   - Чат: http://localhost:8000/chat
   - Админ-панель: http://localhost:8000/admin
   - API документация: http://localhost:8000/docs

### Авторизация по умолчанию

- **Логин:** admin
- **Пароль:** admin

⚠️ **Важно:** Смените пароль после первого входа!

## 📚 Документация

- [🚀 QUICK_START.md](QUICK_START.md) - Быстрый старт после обновления
- [📖 UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) - Подробное руководство по обновлению
- [📝 CHANGELOG_ARTICLES.md](CHANGELOG_ARTICLES.md) - История изменений статей

## 🎯 Недавние улучшения (v2.0)

### Улучшена работа с русским языком:

✅ **Новые multilingual модели:**
- Embeddings: `paraphrase-multilingual-MiniLM-L12-v2`
- Reranker: `mmarco-mMiniLMv2-L12-H384-v1`
- LLM: `qwen2.5:7b`

✅ **Улучшенные параметры:**
- Размер чанка увеличен до 800 символов
- Поиск расширен до top-30 результатов

✅ **Постобработка ответов:**
- Автоматическая фильтрация артефактов
- Строгий контроль языка ответа

## 🏗️ Архитектура

```
RAG Pipeline:
1. Chunking    → Разбиение документов на чанки
2. Embedding   → Векторизация с multilingual моделью
3. Retrieval   → Поиск релевантных чанков (top-30)
4. Reranking   → Переранжирование с cross-encoder (top-5)
5. Generation  → Генерация ответа с LLM (Qwen 2.5)
```

## 📁 Структура проекта

```
.
├── api/              # FastAPI endpoints
├── auth/             # Авторизация и пользователи
├── config/           # Конфигурация
├── database/         # БД статей и сессий
├── data/             # Данные и ChromaDB
├── frontend/         # UI (HTML/CSS/JS)
├── rag/              # RAG pipeline компоненты
├── scripts/          # Утилиты
├── utils/            # Вспомогательные модули
├── main.py           # Точка входа
├── reindex_articles.py  # Скрипт переиндексации
└── requirements.txt  # Зависимости
```

## 🛠️ Основные команды

### Управление статьями
```bash
# Переиндексация всех статей
python reindex_articles.py

# Генерация тестовых статей
python generate_articles.py
```

### Запуск системы
```bash
# Запуск сервера
python main.py

# Проверка работоспособности
curl http://localhost:8000/health
```

## 🔧 Настройка

Основные параметры находятся в [main.py](main.py):

```python
RAGPipeline(
    chunk_size=800,           # Размер чанка
    chunk_overlap=100,        # Перекрытие чанков
    embedding_model="...",    # Модель эмбеддингов
    reranker_model="...",     # Модель reranker
    llm_model="qwen2.5:7b",  # LLM модель
    retrieval_top_k=30,       # Кол-во результатов поиска
    rerank_top_k=5           # Кол-во после reranking
)
```

## 📊 API Endpoints

### Публичные
- `POST /login` - Авторизация
- `POST /register` - Регистрация
- `POST /ask` - Задать вопрос (требует авторизации)
- `GET /health` - Проверка работоспособности

### Админ-панель (требует роль admin)
- `GET /admin/articles` - Список статей
- `POST /admin/articles` - Создать статью
- `PUT /admin/articles/{id}` - Обновить статью
- `DELETE /admin/articles/{id}` - Удалить статью
- `POST /admin/rag/reindex` - Переиндексация
- `GET /admin/analytics/overview` - Аналитика

## 🐛 Устранение проблем

### Проблема: "Cannot connect to Ollama"
```bash
# Запустите Ollama
ollama serve
```

### Проблема: "Model not found"
```bash
# Установите модель
ollama pull qwen2.5:7b
```

### Проблема: Низкое качество ответов
```bash
# Переиндексируйте статьи
python reindex_articles.py
```

## 📝 Лицензия

Proprietary - Все права защищены

## 👨‍💻 Автор

AI_Assistent_for_Dima - Система рекомендаций на основе RAG