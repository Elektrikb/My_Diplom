# File: rag/reranker.py
"""
Модуль для reranking результатов поиска с использованием cross-encoder
"""
import logging
from typing import List, Dict
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    """Класс для переранжирования результатов поиска"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Args:
            model_name: Имя модели cross-encoder
        """
        self.model_name = model_name
        try:
            self.model = CrossEncoder(model_name)
            logger.info(f"Initialized cross-encoder: {model_name}")
        except Exception as e:
            logger.error(f"Error loading cross-encoder model: {e}")
            raise

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Переранжировать чанки на основе релевантности к запросу

        Args:
            query: Поисковый запрос
            chunks: Список чанков с метаданными
            top_k: Количество лучших результатов для возврата

        Returns:
            Список переранжированных чанков с обновленными scores
        """
        if not chunks:
            logger.warning("No chunks to rerank")
            return []

        try:
            # Подготовка пар (query, chunk_text) для cross-encoder
            pairs = [[query, chunk['text']] for chunk in chunks]

            # Вычисление scores с помощью cross-encoder
            logger.debug(f"Reranking {len(chunks)} chunks...")
            scores = self.model.predict(pairs, show_progress_bar=False)

            # Добавление scores к чанкам
            for chunk, score in zip(chunks, scores):
                chunk['rerank_score'] = float(score)

            # Сортировка по rerank_score
            reranked_chunks = sorted(
                chunks,
                key=lambda x: x['rerank_score'],
                reverse=True
            )

            # Возвращаем top_k
            result = reranked_chunks[:top_k]

            logger.debug(f"Reranked and selected top {len(result)} chunks")
            return result

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback: возвращаем оригинальные чанки
            return chunks[:top_k]

    def get_best_chunk(self, query: str, chunks: List[Dict]) -> Dict:
        """
        Получить самый релевантный чанк

        Args:
            query: Поисковый запрос
            chunks: Список чанков

        Returns:
            Самый релевантный чанк
        """
        reranked = self.rerank(query, chunks, top_k=1)
        return reranked[0] if reranked else {}
