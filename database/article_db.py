# File: database/article_db.py
import json
import sqlite3
import numpy as np
from typing import List, Dict, Optional
import logging
from .db_init import get_connection, init_database, get_db_path

logger = logging.getLogger(__name__)


class ArticleDatabase:
    def __init__(self, articles_path: str = None, excel_path: Optional[str] = None):
        """
        Инициализация базы данных статей.

        Args:
            articles_path: Устаревший параметр, сохранен для совместимости
            excel_path: Путь к Excel файлу для первичной загрузки (если БД пуста)
        """
        self.db_path = get_db_path()
        self.excel_path = excel_path

        # Инициализируем БД
        init_database(self.db_path)

        # Загружаем статьи из БД
        self.articles = self._load_articles()

        # Инициализируем энкодер только если есть статьи
        if self.articles:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.article_embeddings = self._encode_articles()
        else:
            self.encoder = None
            self.article_embeddings = np.array([])

    def _get_conn(self) -> sqlite3.Connection:
        """Получить соединение с БД"""
        return get_connection(self.db_path)

    def _load_articles(self) -> List[Dict]:
        """Загрузка статей из SQLite"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, url, tags FROM articles ORDER BY id")
            articles = []
            for row in cursor.fetchall():
                # Парсим теги из JSON строки
                tags = []
                if row[4]:
                    try:
                        tags = json.loads(row[4])
                    except json.JSONDecodeError:
                        tags = []

                articles.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "url": row[3],
                    "tags": tags
                })

            if articles:
                logger.info(f"Loaded {len(articles)} articles from SQLite")
            return articles
        finally:
            conn.close()

    def _encode_articles(self) -> np.ndarray:
        """Создание эмбеддингов для всех статей"""
        if not self.articles:
            return np.array([])

        try:
            texts = [f"{article['title']} {article['content'][:500]}" for article in self.articles]
            embeddings = self.encoder.encode(texts)
            logger.info(f"Encoded {len(embeddings)} article embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding articles: {e}")
            return np.array([])

    def get_article(self, article_id: int) -> Optional[Dict]:
        """Получить статью по ID"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, content, url, tags FROM articles WHERE id = ?",
                (article_id,)
            )
            row = cursor.fetchone()
            if row:
                tags = []
                if row[4]:
                    try:
                        tags = json.loads(row[4])
                    except json.JSONDecodeError:
                        tags = []

                return {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "url": row[3],
                    "tags": tags
                }
            logger.warning(f"Article ID {article_id} not found")
            return None
        finally:
            conn.close()

    def get_article_embedding(self, article_id: int) -> Optional[np.ndarray]:
        """Получить эмбеддинг статьи"""
        # Находим индекс статьи в кеше
        for i, article in enumerate(self.articles):
            if article['id'] == article_id:
                if i < len(self.article_embeddings):
                    return self.article_embeddings[i]
        return None

    def get_all_articles(self) -> List[Dict]:
        """Получить все статьи"""
        # Возвращаем закешированный список для совместимости
        return self.articles

    def search_similar_articles(self, query: str, top_k: int = 5) -> List[Dict]:
        """Поиск похожих статей по запросу"""
        if not self.articles or len(self.article_embeddings) == 0:
            return []

        try:
            query_embedding = self.encoder.encode([query])
            similarities = np.dot(self.article_embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            results = [self.articles[i] for i in top_indices]
            logger.debug(f"Semantic search found {len(results)} articles for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return self.articles[:top_k]

    def add_article(self, article_dict: Dict) -> int:
        """Добавление новой статьи"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            tags_json = json.dumps(article_dict.get('tags', []), ensure_ascii=False)

            cursor.execute(
                "INSERT INTO articles (title, content, url, tags) VALUES (?, ?, ?, ?)",
                (
                    article_dict.get('title', ''),
                    article_dict.get('content', ''),
                    article_dict.get('url', ''),
                    tags_json
                )
            )
            conn.commit()
            new_id = cursor.lastrowid

            # Обновляем кеш
            article_dict['id'] = new_id
            self.articles.append(article_dict)

            # Генерируем embedding для новой статьи
            if self.encoder:
                text = f"{article_dict['title']} {article_dict['content'][:500]}"
                new_embedding = self.encoder.encode([text])

                if len(self.article_embeddings) > 0:
                    self.article_embeddings = np.vstack([self.article_embeddings, new_embedding])
                else:
                    self.article_embeddings = new_embedding

            logger.info(f"Added article {new_id}: {article_dict['title']}")
            return new_id

        except Exception as e:
            logger.error(f"Error adding article: {e}")
            raise
        finally:
            conn.close()

    def update_article(self, article_id: int, update_data: Dict) -> bool:
        """Обновление статьи"""
        conn = self._get_conn()
        try:
            # Получаем текущую статью
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, url, tags FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Article {article_id} not found for update")
                return False

            # Формируем данные для обновления
            current = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "url": row[3],
                "tags": json.loads(row[4]) if row[4] else []
            }

            # Проверяем нужен ли пересчет embedding
            needs_reembedding = (
                ('title' in update_data and update_data['title'] != current['title']) or
                ('content' in update_data and update_data['content'] != current['content'])
            )

            # Применяем обновления
            for key, value in update_data.items():
                current[key] = value

            # Сохраняем в БД
            tags_json = json.dumps(current.get('tags', []), ensure_ascii=False)
            cursor.execute(
                "UPDATE articles SET title = ?, content = ?, url = ?, tags = ? WHERE id = ?",
                (current['title'], current['content'], current['url'], tags_json, article_id)
            )
            conn.commit()

            # Обновляем кеш
            for i, article in enumerate(self.articles):
                if article['id'] == article_id:
                    self.articles[i] = current

                    # Пересчитываем embedding если нужно
                    if needs_reembedding and self.encoder and i < len(self.article_embeddings):
                        text = f"{current['title']} {current['content'][:500]}"
                        new_embedding = self.encoder.encode([text])
                        self.article_embeddings[i] = new_embedding[0]
                    break

            logger.info(f"Updated article {article_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            return False
        finally:
            conn.close()

    def delete_article(self, article_id: int) -> bool:
        """Удаление статьи"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Находим индекс в кеше
            article_index = None
            for i, article in enumerate(self.articles):
                if article['id'] == article_id:
                    article_index = i
                    break

            if article_index is None:
                logger.warning(f"Article {article_id} not found for deletion")
                return False

            # Удаляем из БД
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return False

            # Удаляем из кеша
            deleted_article = self.articles.pop(article_index)

            # Удаляем embedding
            if article_index < len(self.article_embeddings):
                self.article_embeddings = np.delete(self.article_embeddings, article_index, axis=0)

            logger.info(f"Deleted article {article_id}: {deleted_article['title']}")
            return True

        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
        finally:
            conn.close()

    def get_articles_paginated(self, offset: int = 0, limit: int = 10,
                               search: str = None, tags: List[str] = None) -> Dict:
        """Получение статей с пагинацией и фильтрацией"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Базовый запрос
            query = "SELECT id, title, content, url, tags FROM articles WHERE 1=1"
            params = []

            # Фильтрация по поисковому запросу
            if search:
                query += " AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)"
                search_pattern = f"%{search.lower()}%"
                params.extend([search_pattern, search_pattern])

            # Получаем общее количество
            count_query = query.replace("SELECT id, title, content, url, tags", "SELECT COUNT(*)")
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Добавляем пагинацию
            query += " ORDER BY id LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            articles = []

            for row in cursor.fetchall():
                article_tags = []
                if row[4]:
                    try:
                        article_tags = json.loads(row[4])
                    except json.JSONDecodeError:
                        article_tags = []

                # Фильтрация по тегам (в Python, так как SQLite не поддерживает JSON массивы нативно)
                if tags:
                    if not any(tag in article_tags for tag in tags):
                        continue

                articles.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "url": row[3],
                    "tags": article_tags
                })

            # Если фильтровали по тегам, пересчитываем total
            if tags:
                # Для точного подсчета с тегами нужно загрузить все
                cursor.execute(
                    "SELECT tags FROM articles WHERE 1=1" +
                    (" AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)" if search else ""),
                    params[:-2] if search else []
                )
                total = sum(
                    1 for row in cursor.fetchall()
                    if row[0] and any(tag in json.loads(row[0]) for tag in tags)
                )

            return {
                "articles": articles,
                "total": total,
                "offset": offset,
                "limit": limit
            }

        except Exception as e:
            logger.error(f"Error in paginated articles query: {e}")
            return {
                "articles": [],
                "total": 0,
                "offset": offset,
                "limit": limit
            }
        finally:
            conn.close()

    def reload_from_db(self):
        """Перезагрузить статьи из БД (для синхронизации после миграции)"""
        self.articles = self._load_articles()
        if self.articles and self.encoder:
            self.article_embeddings = self._encode_articles()
        logger.info(f"Reloaded {len(self.articles)} articles from database")
