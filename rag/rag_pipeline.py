# File: rag/rag_pipeline.py
"""
Главный модуль RAG pipeline, объединяющий все компоненты
"""
import logging
from typing import List, Dict, Optional
from .chunker import DocumentChunker
from .vector_store import VectorStore
from .reranker import Reranker
from .llm_generator import LLMGenerator

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Полный RAG (Retrieval-Augmented Generation) pipeline

    Pipeline:
    1. Chunking - разбиение документов на чанки
    2. Vector Search - векторный поиск релевантных чанков
    3. Reranking - переранжирование с cross-encoder
    4. Generation - генерация ответа с LLM
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "articles",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        llm_model: str = "llama3.2",
        llm_base_url: str = "http://localhost:11434",
        retrieval_top_k: int = 20,
        rerank_top_k: int = 5
    ):
        """
        Args:
            chunk_size: Размер чанка в символах
            chunk_overlap: Перекрытие между чанками
            persist_directory: Директория для ChromaDB
            collection_name: Имя коллекции
            embedding_model: Модель для эмбеддингов
            reranker_model: Модель для reranking
            llm_model: Модель Ollama для генерации
            llm_base_url: URL Ollama API
            retrieval_top_k: Количество чанков для начального поиска
            rerank_top_k: Количество чанков после reranking
        """
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_k = rerank_top_k

        # Инициализация компонентов
        logger.info("Initializing RAG Pipeline...")

        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        logger.info("✓ Document chunker initialized")

        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        logger.info("✓ Vector store initialized")

        self.reranker = Reranker(model_name=reranker_model)
        logger.info("✓ Reranker initialized")

        self.llm_generator = LLMGenerator(
            model_name=llm_model,
            base_url=llm_base_url
        )
        logger.info("✓ LLM generator initialized")

        logger.info("RAG Pipeline initialization complete!")

    def index_articles(self, articles: List[Dict], rebuild: bool = False):
        """
        Индексировать статьи в векторное хранилище

        Args:
            articles: Список статей
            rebuild: Пересоздать индекс с нуля
        """
        logger.info(f"Indexing {len(articles)} articles...")

        # Разбиваем статьи на чанки
        chunks = self.chunker.chunk_articles(articles)

        # Добавляем в векторное хранилище
        if rebuild:
            self.vector_store.rebuild_index(chunks)
        else:
            self.vector_store.add_chunks(chunks)

        logger.info(f"Indexing complete! Total chunks: {len(chunks)}")

    def query(
        self,
        question: str,
        language: str = "ru",
        filter_dict: Optional[Dict] = None
    ) -> Dict:
        """
        Выполнить полный RAG pipeline для ответа на вопрос

        Args:
            question: Вопрос пользователя
            language: Язык ответа
            filter_dict: Фильтры для поиска

        Returns:
            Словарь с ответом, источниками и метаданными
        """
        try:
            logger.info(f"Processing question: {question[:100]}...")

            # Шаг 1: Векторный поиск
            logger.debug(f"Step 1: Vector search (top_k={self.retrieval_top_k})...")
            retrieved_chunks = self.vector_store.search(
                query=question,
                top_k=self.retrieval_top_k,
                filter_dict=filter_dict
            )

            if not retrieved_chunks:
                logger.warning("No chunks retrieved from vector search")
                return {
                    'answer': "К сожалению, не удалось найти релевантную информацию для ответа на ваш вопрос.",
                    'sources': [],
                    'num_chunks_retrieved': 0,
                    'num_chunks_reranked': 0,
                    'pipeline_steps': {
                        'retrieval': 0,
                        'reranking': 0,
                        'generation': 'skipped'
                    }
                }

            logger.info(f"Retrieved {len(retrieved_chunks)} chunks from vector search")

            # Шаг 2: Reranking
            logger.debug(f"Step 2: Reranking (top_k={self.rerank_top_k})...")
            reranked_chunks = self.reranker.rerank(
                query=question,
                chunks=retrieved_chunks,
                top_k=self.rerank_top_k
            )

            logger.info(f"Reranked to {len(reranked_chunks)} best chunks")

            # Шаг 3: Генерация ответа с LLM
            logger.debug("Step 3: Generating answer with LLM...")
            result = self.llm_generator.generate(
                question=question,
                context_chunks=reranked_chunks,
                language=language
            )

            # Добавляем метаданные о pipeline
            result['num_chunks_retrieved'] = len(retrieved_chunks)
            result['num_chunks_reranked'] = len(reranked_chunks)
            result['pipeline_steps'] = {
                'retrieval': len(retrieved_chunks),
                'reranking': len(reranked_chunks),
                'generation': 'success' if result.get('model') != 'fallback' else 'fallback'
            }

            logger.info("RAG pipeline completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                'answer': f"Произошла ошибка при обработке вопроса: {str(e)}",
                'sources': [],
                'error': str(e)
            }

    def get_stats(self) -> Dict:
        """Получить статистику RAG pipeline"""
        vector_stats = self.vector_store.get_stats()
        return {
            'vector_store': vector_stats,
            'chunk_size': self.chunker.chunk_size,
            'chunk_overlap': self.chunker.chunk_overlap,
            'retrieval_top_k': self.retrieval_top_k,
            'rerank_top_k': self.rerank_top_k,
            'llm_model': self.llm_generator.model_name
        }

    def clear_index(self):
        """Очистить векторный индекс"""
        self.vector_store.clear_collection()
        logger.info("Vector index cleared")
