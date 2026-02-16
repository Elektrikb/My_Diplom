# -*- coding: utf-8 -*-
"""
Скрипт для переиндексации всех статей в векторное хранилище

🔄 КОГДА ИСПОЛЬЗОВАТЬ:
  - После обновления моделей эмбеддингов или reranker
  - После добавления большого количества новых статей
  - После изменения параметров chunking (chunk_size, chunk_overlap)
  - При проблемах с качеством поиска

⚡ ЧТО ДЕЛАЕТ:
  - Загружает все статьи из базы данных
  - Разбивает их на чанки с новыми параметрами
  - Создает векторные эмбеддинги с новой моделью
  - Полностью пересоздает индекс ChromaDB

⚠️  ВАЖНО:
  - Процесс может занять несколько минут в зависимости от количества статей
  - Требуется подключение к Ollama (для RAG Pipeline)
  - Старый индекс будет полностью удален и пересоздан
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.article_db import ArticleDatabase
from rag.rag_pipeline import RAGPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("="*60)
        logger.info("Начинаем переиндексацию статей...")
        logger.info("="*60)

        # Загружаем все статьи из базы данных
        article_db = ArticleDatabase()
        articles = article_db.get_all_articles()
        logger.info(f"Загружено {len(articles)} статей из базы данных")

        if not articles:
            logger.error("В базе данных нет статей!")
            return

        # Показываем статистику по URL
        articles_with_url = sum(1 for a in articles if a.get('url'))
        articles_without_url = len(articles) - articles_with_url
        logger.info(f"  - Статей с внешним URL: {articles_with_url}")
        logger.info(f"  - Статей без URL (внутренние): {articles_without_url}")

        # Инициализируем RAG Pipeline с ОБНОВЛЕННЫМИ параметрами
        logger.info("\nИнициализация RAG Pipeline с улучшенными multilingual моделями...")
        logger.info("  📚 Embedding: paraphrase-multilingual-MiniLM-L12-v2")
        logger.info("  🔄 Reranker: mmarco-mMiniLMv2-L12-H384-v1")
        logger.info("  🤖 LLM: qwen2.5:7b")
        logger.info("  📏 Chunk size: 800, overlap: 100")

        rag_pipeline = RAGPipeline(
            chunk_size=800,  # Увеличено для лучшего контекста
            chunk_overlap=100,  # Увеличено для плавного перехода
            persist_directory="data/chroma_db",
            collection_name="articles",
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Multilingual модель
            reranker_model="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Multilingual reranker
            llm_model="qwen2.5:7b",  # Модель с отличной поддержкой русского
            llm_base_url="http://localhost:11434",
            retrieval_top_k=30,  # Увеличено для лучшего покрытия
            rerank_top_k=5
        )

        # Полная переиндексация (rebuild=True)
        logger.info("\nНачинаем полную переиндексацию (rebuild=True)...")
        rag_pipeline.index_articles(articles, rebuild=True)

        # Получаем статистику
        stats = rag_pipeline.get_stats()
        logger.info("\n" + "="*60)
        logger.info("Переиндексация завершена успешно!")
        logger.info("="*60)
        logger.info(f"Статистика векторного хранилища:")
        logger.info(f"  - Коллекция: {stats['vector_store']['collection_name']}")
        logger.info(f"  - Всего чанков: {stats['vector_store']['total_chunks']}")
        logger.info(f"  - Размер чанка: {stats['chunk_size']} символов")
        logger.info(f"  - Перекрытие: {stats['chunk_overlap']} символов")
        logger.info(f"  - Директория: {stats['vector_store']['persist_directory']}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"\nОшибка при переиндексации: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
