# File: database/db_init.py
import sqlite3
import os
from contextlib import contextmanager
from typing import Optional

# Путь к базе данных по умолчанию
DEFAULT_DB_PATH = "data/app.db"


def get_db_path() -> str:
    """Получить путь к базе данных из конфигурации или использовать значение по умолчанию"""
    try:
        from config.settings import Config
        return getattr(Config, 'DATABASE_PATH', DEFAULT_DB_PATH)
    except ImportError:
        return DEFAULT_DB_PATH


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Создать соединение с базой данных"""
    if db_path is None:
        db_path = get_db_path()

    # Создаем директорию если не существует
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
    conn.execute("PRAGMA foreign_keys = ON")  # Включаем foreign keys
    return conn


@contextmanager
def get_db_cursor(db_path: Optional[str] = None):
    """Context manager для работы с курсором базы данных"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_database(db_path: Optional[str] = None):
    """Инициализация базы данных - создание всех таблиц"""
    if db_path is None:
        db_path = get_db_path()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT 'user' CHECK(role IN ('admin', 'user')),
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Таблица статей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT,
                tags TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title)')

        # Таблица сессий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                total_reward REAL DEFAULT 0.0,
                interaction_count INTEGER DEFAULT 0
            )
        ''')

        # Таблица взаимодействий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_query TEXT NOT NULL,
                article_id INTEGER,
                article_title TEXT,
                article_url TEXT,
                reward REAL DEFAULT 0.0,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_article ON interactions(article_id)')

        # Таблица для отслеживания очистки истории чата (только для UI, данные сохраняются)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_clear_history (
                user_id TEXT PRIMARY KEY,
                cleared_at TEXT NOT NULL
            )
        ''')

        conn.commit()
        print(f"Database initialized at {db_path}")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def verify_database(db_path: Optional[str] = None) -> dict:
    """Проверка целостности базы данных и получение статистики"""
    if db_path is None:
        db_path = get_db_path()

    stats = {}

    with get_db_cursor(db_path) as cursor:
        # Проверяем наличие таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        stats['tables'] = tables

        # Считаем записи в каждой таблице
        for table in ['users', 'articles', 'sessions', 'interactions']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            else:
                stats[f'{table}_count'] = 0

    return stats


if __name__ == "__main__":
    # Тестовый запуск
    init_database()
    stats = verify_database()
    print(f"Database stats: {stats}")
