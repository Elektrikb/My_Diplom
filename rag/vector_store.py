# File: rag/vector_store.py
"""
Модуль для работы с векторным хранилищем ChromaDB
"""
import logging
import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """Класс для работы с векторным хранилищем ChromaDB"""

    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "articles",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Args:
            persist_directory: Директория для хранения БД
            collection_name: Имя коллекции
            embedding_model: Модель для создания эмбеддингов
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Создаем директорию если не существует
        os.makedirs(persist_directory, exist_ok=True)

        # Инициализируем ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Инициализируем модель эмбеддингов
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"Initialized embedding model: {embedding_model}")

        # Получаем или создаем коллекцию
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection '{collection_name}' with {self.collection.count()} documents")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Article chunks for RAG"}
            )
            logger.info(f"Created new collection '{collection_name}'")

    def add_chunks(self, chunks: List[Dict]):
        """
        Добавить чанки в векторное хранилище

        Args:
            chunks: Список чанков с метаданными
        """
        if not chunks:
            logger.warning("No chunks to add")
            return

        try:
            # Подготовка данных
            texts = [chunk['text'] for chunk in chunks]
            ids = [f"{chunk['article_id']}_{chunk['chunk_index']}" for chunk in chunks]

            # Создание метаданных (ChromaDB требует, чтобы все значения были примитивными типами)
            metadatas = []
            for chunk in chunks:
                metadata = {
                    'article_id': str(chunk['article_id']),
                    'article_title': chunk['article_title'],
                    'article_url': chunk['article_url'] if chunk['article_url'] is not None else '',  # None -> пустая строка
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'tags': ','.join(chunk.get('tags', []))  # Преобразуем список в строку
                }
                metadatas.append(metadata)

            # Создание эмбеддингов
            logger.info(f"Creating embeddings for {len(texts)} chunks...")
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=True,
                convert_to_numpy=True
            )

            # Добавление в ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} chunks to vector store")

        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Поиск релевантных чанков по запросу

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            filter_dict: Фильтры для метаданных

        Returns:
            Список релевантных чанков с метаданными и scores
        """
        try:
            # Создание эмбеддинга запроса
            query_embedding = self.embedding_model.encode([query])[0]

            # Поиск в ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_dict,
                include=['documents', 'metadatas', 'distances']
            )

            # Преобразование результатов
            chunks = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    chunk = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'score': 1 / (1 + results['distances'][0][i])  # Конвертируем distance в score
                    }
                    # Восстанавливаем список тегов
                    if 'tags' in chunk['metadata']:
                        tags_str = chunk['metadata']['tags']
                        chunk['metadata']['tags'] = tags_str.split(',') if tags_str else []

                    chunks.append(chunk)

            logger.debug(f"Found {len(chunks)} chunks for query: {query[:50]}...")
            return chunks

        except Exception as e:
            logger.error(f"Error searching in vector store: {e}")
            return []

    def clear_collection(self):
        """Очистить коллекцию"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Article chunks for RAG"}
            )
            logger.info(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def rebuild_index(self, chunks: List[Dict]):
        """
        Пересоздать индекс с новыми чанками

        Args:
            chunks: Список чанков
        """
        logger.info("Rebuilding vector index...")
        self.clear_collection()
        self.add_chunks(chunks)
        logger.info("Vector index rebuilt successfully")

    def get_stats(self) -> Dict:
        """Получить статистику по коллекции"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'total_chunks': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
