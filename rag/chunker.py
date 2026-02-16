# File: rag/chunker.py
"""
Модуль для разбиения документов на чанки (chunks)
"""
import logging
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunker:
    """Класс для разбиения документов на чанки"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: Размер чанка в символах
            chunk_overlap: Перекрытие между чанками в символах
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Используем RecursiveCharacterTextSplitter для умного разбиения
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_article(self, article: Dict) -> List[Dict]:
        """
        Разбить статью на чанки

        Args:
            article: Словарь со статьей (должен содержать 'id', 'title', 'content', 'url')

        Returns:
            Список чанков с метаданными
        """
        try:
            # Объединяем title и content для разбиения
            full_text = f"{article['title']}\n\n{article['content']}"

            # Разбиваем на чанки
            text_chunks = self.text_splitter.split_text(full_text)

            # Создаем чанки с метаданными
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk = {
                    'text': chunk_text,
                    'article_id': article['id'],
                    'article_title': article['title'],
                    'article_url': article['url'],
                    'chunk_index': i,
                    'total_chunks': len(text_chunks),
                    'tags': article.get('tags', [])
                }
                chunks.append(chunk)

            logger.debug(f"Split article {article['id']} into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking article {article.get('id', 'unknown')}: {e}")
            return []

    def chunk_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Разбить список статей на чанки

        Args:
            articles: Список статей

        Returns:
            Список всех чанков из всех статей
        """
        all_chunks = []
        for article in articles:
            chunks = self.chunk_article(article)
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(articles)} articles")
        return all_chunks
