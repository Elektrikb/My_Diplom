# File: database/session_manager.py
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from .db_init import get_connection, init_database, get_db_path


class SessionManager:
    def __init__(self, sessions_path: str = None):
        """
        Инициализация менеджера сессий.

        Args:
            sessions_path: Устаревший параметр, сохранен для совместимости
        """
        self.db_path = get_db_path()
        init_database(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Получить соединение с БД"""
        return get_connection(self.db_path)

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Создание новой сессии"""
        if user_id is None:
            user_id = str(uuid.uuid4())

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                """INSERT OR REPLACE INTO sessions
                   (session_id, created_at, updated_at, total_reward, interaction_count)
                   VALUES (?, ?, ?, 0.0, 0)""",
                (user_id, now, now)
            )
            conn.commit()
            return user_id
        finally:
            conn.close()

    def add_interaction(self, user_id: str, user_query: str,
                        recommended_article: Dict, reward: float):
        """Добавление взаимодействия в историю сессии"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Проверяем существует ли сессия
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (user_id,))
            if not cursor.fetchone():
                self.create_session(user_id)

            # Добавляем взаимодействие
            cursor.execute(
                """INSERT INTO interactions
                   (session_id, timestamp, user_query, article_id, article_title, article_url, reward)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    datetime.now().isoformat(),
                    user_query,
                    recommended_article.get('id'),
                    recommended_article.get('title', ''),
                    recommended_article.get('url', ''),
                    reward
                )
            )

            # Обновляем статистику сессии
            cursor.execute(
                """UPDATE sessions SET
                   total_reward = total_reward + ?,
                   interaction_count = interaction_count + 1,
                   updated_at = ?
                   WHERE session_id = ?""",
                (reward, datetime.now().isoformat(), user_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_session_history(self, user_id: str) -> List[Dict]:
        """Получение истории сессии"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT timestamp, user_query, article_id, article_title, article_url, reward
                   FROM interactions
                   WHERE session_id = ?
                   ORDER BY timestamp""",
                (user_id,)
            )

            return [
                {
                    'timestamp': row[0],
                    'user_query': row[1],
                    'recommended_article': {
                        'id': row[2],
                        'title': row[3],
                        'url': row[4]
                    },
                    'reward': row[5]
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def get_formatted_chat_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Получение истории чата в формате для UI (только записи после последней очистки)"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Получаем timestamp последней очистки истории
            cursor.execute(
                "SELECT cleared_at FROM chat_clear_history WHERE user_id = ?",
                (user_id,)
            )
            clear_row = cursor.fetchone()
            cleared_at = clear_row[0] if clear_row else None

            # Получаем только сообщения после последней очистки
            if cleared_at:
                cursor.execute(
                    """SELECT timestamp, user_query, article_id, article_title, article_url
                       FROM interactions
                       WHERE session_id = ? AND timestamp > ?
                       ORDER BY timestamp ASC
                       LIMIT ?""",
                    (user_id, cleared_at, limit)
                )
            else:
                cursor.execute(
                    """SELECT timestamp, user_query, article_id, article_title, article_url
                       FROM interactions
                       WHERE session_id = ?
                       ORDER BY timestamp ASC
                       LIMIT ?""",
                    (user_id, limit)
                )

            messages = []
            for row in cursor.fetchall():
                timestamp = row[0]

                # Сообщение пользователя
                messages.append({
                    'timestamp': timestamp,
                    'sender': 'user',
                    'message': row[1],
                    'article': None
                })

                # Ответ бота (если есть рекомендованная статья)
                if row[2] is not None:
                    messages.append({
                        'timestamp': timestamp,
                        'sender': 'bot',
                        'message': f'Рекомендую ознакомиться со статьёй: {row[3]}',
                        'article': {
                            'id': row[2],
                            'title': row[3],
                            'url': row[4]
                        }
                    })

            return messages
        finally:
            conn.close()

    def clear_chat_history(self, user_id: str) -> bool:
        """Очистка истории чата пользователя (скрывает из UI, но сохраняет в БД для аналитики)"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            # Сохраняем timestamp очистки (вместо удаления записей)
            cursor.execute(
                """INSERT OR REPLACE INTO chat_clear_history (user_id, cleared_at)
                   VALUES (?, ?)""",
                (user_id, now)
            )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_session_stats(self, user_id: str) -> Optional[Dict]:
        """Получение статистики сессии"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT session_id, created_at, total_reward, interaction_count
                   FROM sessions WHERE session_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                interaction_count = row[3]
                total_reward = row[2]
                avg_reward = total_reward / interaction_count if interaction_count > 0 else 0

                return {
                    'user_id': row[0],
                    'created_at': row[1],
                    'interaction_count': interaction_count,
                    'total_reward': total_reward,
                    'avg_reward': avg_reward
                }
            return None
        finally:
            conn.close()

    def get_global_analytics(self) -> Dict:
        """Общая аналитика системы"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Общая статистика сессий
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), SUM(reward) FROM interactions")
            row = cursor.fetchone()
            total_interactions = row[0] or 0
            total_reward = row[1] or 0

            # Статистика по статьям
            cursor.execute(
                """SELECT article_id, COUNT(*) as cnt, SUM(reward) as total_reward
                   FROM interactions
                   WHERE article_id IS NOT NULL
                   GROUP BY article_id
                   ORDER BY cnt DESC
                   LIMIT 10"""
            )

            top_articles = [
                {
                    "article_id": row[0],
                    "recommendation_count": row[1],
                    "total_reward": row[2] or 0,
                    "avg_reward": (row[2] or 0) / row[1] if row[1] > 0 else 0
                }
                for row in cursor.fetchall()
            ]

            return {
                "total_sessions": total_sessions,
                "total_interactions": total_interactions,
                "total_reward": total_reward,
                "avg_reward": total_reward / total_interactions if total_interactions > 0 else 0,
                "top_articles": top_articles
            }
        finally:
            conn.close()

    def get_article_analytics(self, article_id: int) -> Dict:
        """Аналитика по конкретной статье"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """SELECT COUNT(*), SUM(reward), COUNT(DISTINCT session_id)
                   FROM interactions
                   WHERE article_id = ?""",
                (article_id,)
            )
            row = cursor.fetchone()

            count = row[0] or 0
            total_reward = row[1] or 0
            unique_users = row[2] or 0

            return {
                "article_id": article_id,
                "recommendation_count": count,
                "total_reward": total_reward,
                "avg_reward": total_reward / count if count > 0 else 0,
                "unique_users": unique_users
            }
        finally:
            conn.close()

    def get_timeline_analytics(self, days: int = 7) -> Dict:
        """Аналитика по временной шкале"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute(
                """SELECT DATE(timestamp) as date, COUNT(*) as interactions, SUM(reward) as total_reward
                   FROM interactions
                   WHERE timestamp >= ?
                   GROUP BY DATE(timestamp)
                   ORDER BY date""",
                (cutoff,)
            )

            timeline = [
                {
                    "date": row[0],
                    "interactions": row[1],
                    "total_reward": row[2] or 0,
                    "avg_reward": (row[2] or 0) / row[1] if row[1] > 0 else 0
                }
                for row in cursor.fetchall()
            ]

            return {
                "period_days": days,
                "timeline": timeline
            }
        finally:
            conn.close()

    @property
    def sessions(self) -> Dict[str, Dict]:
        """Свойство для обратной совместимости - возвращает словарь всех сессий"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_id, created_at, updated_at, total_reward, interaction_count FROM sessions"
            )

            result = {}
            for row in cursor.fetchall():
                session_id = row[0]
                result[session_id] = {
                    'created_at': row[1],
                    'updated_at': row[2],
                    'total_reward': row[3],
                    'interaction_count': row[4],
                    'conversation_history': self.get_session_history(session_id)
                }

            return result
        finally:
            conn.close()
