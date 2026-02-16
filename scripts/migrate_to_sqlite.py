#!/usr/bin/env python3
"""
Скрипт миграции данных из JSON в SQLite.

Использование:
    python scripts/migrate_to_sqlite.py

Скрипт автоматически:
1. Создает базу данных SQLite
2. Переносит данные из JSON файлов
3. Верифицирует целостность данных
"""

import json
import os
import sys

# Добавляем корневую директорию проекта в путь
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from database.db_init import init_database, get_connection, verify_database

# Пути к файлам
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
USERS_JSON = os.path.join(DATA_DIR, "users.json")
ARTICLES_JSON = os.path.join(DATA_DIR, "articles.json")
SESSIONS_JSON = os.path.join(DATA_DIR, "user_sessions.json")
DATABASE_PATH = os.path.join(DATA_DIR, "app.db")


def load_json_file(filepath: str) -> dict | list | None:
    """Загрузить JSON файл"""
    if not os.path.exists(filepath):
        print(f"  [!] Файл не найден: {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"  [!] Файл пустой: {filepath}")
                return None
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [!] Ошибка парсинга JSON {filepath}: {e}")
        return None


def migrate_users(conn) -> int:
    """Миграция пользователей"""
    print("\n[1/3] Миграция пользователей...")

    users_data = load_json_file(USERS_JSON)
    if not users_data:
        print("  Нет данных для миграции")
        return 0

    cursor = conn.cursor()
    migrated = 0

    for username, user_info in users_data.items():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users
                (username, hashed_password, role, created_at, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_info.get('username', username),
                user_info.get('hashed_password', ''),
                user_info.get('role', 'user'),
                user_info.get('created_at', ''),
                1 if user_info.get('is_active', True) else 0
            ))
            migrated += 1
        except Exception as e:
            print(f"  [!] Ошибка при миграции пользователя {username}: {e}")

    conn.commit()
    print(f"  Мигрировано пользователей: {migrated}")
    return migrated


def migrate_articles(conn) -> int:
    """Миграция статей"""
    print("\n[2/3] Миграция статей...")

    articles_data = load_json_file(ARTICLES_JSON)
    if not articles_data:
        print("  Нет данных для миграции")
        return 0

    cursor = conn.cursor()
    migrated = 0

    for article in articles_data:
        try:
            # Теги хранятся как JSON строка
            tags_json = json.dumps(article.get('tags', []), ensure_ascii=False)

            cursor.execute('''
                INSERT OR REPLACE INTO articles
                (id, title, content, url, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                article.get('id'),
                article.get('title', ''),
                article.get('content', ''),
                article.get('url', ''),
                tags_json
            ))
            migrated += 1
        except Exception as e:
            print(f"  [!] Ошибка при миграции статьи {article.get('id')}: {e}")

    conn.commit()
    print(f"  Мигрировано статей: {migrated}")
    return migrated


def migrate_sessions(conn) -> tuple[int, int]:
    """Миграция сессий и взаимодействий"""
    print("\n[3/3] Миграция сессий и взаимодействий...")

    sessions_data = load_json_file(SESSIONS_JSON)
    if not sessions_data:
        print("  Нет данных для миграции")
        return 0, 0

    cursor = conn.cursor()
    sessions_migrated = 0
    interactions_migrated = 0

    for session_id, session_info in sessions_data.items():
        try:
            # Миграция сессии
            cursor.execute('''
                INSERT OR REPLACE INTO sessions
                (session_id, created_at, updated_at, total_reward, interaction_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                session_info.get('created_at', ''),
                session_info.get('updated_at', ''),
                session_info.get('total_reward', 0.0),
                session_info.get('interaction_count', 0)
            ))
            sessions_migrated += 1

            # Миграция взаимодействий
            for interaction in session_info.get('conversation_history', []):
                article = interaction.get('recommended_article', {})
                cursor.execute('''
                    INSERT INTO interactions
                    (session_id, timestamp, user_query, article_id, article_title, article_url, reward)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    interaction.get('timestamp', ''),
                    interaction.get('user_query', ''),
                    article.get('id'),
                    article.get('title', ''),
                    article.get('url', ''),
                    interaction.get('reward', 0.0)
                ))
                interactions_migrated += 1

        except Exception as e:
            print(f"  [!] Ошибка при миграции сессии {session_id}: {e}")

    conn.commit()
    print(f"  Мигрировано сессий: {sessions_migrated}")
    print(f"  Мигрировано взаимодействий: {interactions_migrated}")
    return sessions_migrated, interactions_migrated


def verify_migration(conn) -> bool:
    """Верификация миграции"""
    print("\n[Верификация]")

    # Загружаем исходные данные для сравнения
    users_data = load_json_file(USERS_JSON) or {}
    articles_data = load_json_file(ARTICLES_JSON) or []
    sessions_data = load_json_file(SESSIONS_JSON) or {}

    # Считаем взаимодействия в JSON
    json_interactions = sum(
        len(s.get('conversation_history', []))
        for s in sessions_data.values()
    )

    cursor = conn.cursor()

    # Проверяем количества
    checks = []

    cursor.execute("SELECT COUNT(*) FROM users")
    db_users = cursor.fetchone()[0]
    checks.append(('users', len(users_data), db_users))

    cursor.execute("SELECT COUNT(*) FROM articles")
    db_articles = cursor.fetchone()[0]
    checks.append(('articles', len(articles_data), db_articles))

    cursor.execute("SELECT COUNT(*) FROM sessions")
    db_sessions = cursor.fetchone()[0]
    checks.append(('sessions', len(sessions_data), db_sessions))

    cursor.execute("SELECT COUNT(*) FROM interactions")
    db_interactions = cursor.fetchone()[0]
    checks.append(('interactions', json_interactions, db_interactions))

    all_passed = True
    for table, expected, actual in checks:
        status = "OK" if expected == actual else "FAIL"
        if expected != actual:
            all_passed = False
        print(f"  {table}: JSON={expected}, SQLite={actual} [{status}]")

    return all_passed


def main():
    """Главная функция миграции"""
    print("=" * 60)
    print("МИГРАЦИЯ ДАННЫХ ИЗ JSON В SQLITE")
    print("=" * 60)

    # Проверяем наличие исходных файлов
    print("\n[Проверка исходных файлов]")
    files_exist = True
    for filepath in [USERS_JSON, ARTICLES_JSON, SESSIONS_JSON]:
        exists = os.path.exists(filepath)
        status = "OK" if exists else "НЕ НАЙДЕН"
        print(f"  {os.path.basename(filepath)}: {status}")
        if not exists:
            files_exist = False

    if not files_exist:
        print("\n[!] Некоторые файлы не найдены. Продолжаем с доступными данными...")

    # Инициализация базы данных
    print(f"\n[Инициализация БД: {DATABASE_PATH}]")
    init_database(DATABASE_PATH)

    # Подключаемся к БД
    conn = get_connection(DATABASE_PATH)

    try:
        # Миграция данных
        migrate_users(conn)
        migrate_articles(conn)
        migrate_sessions(conn)

        # Верификация
        success = verify_migration(conn)

        print("\n" + "=" * 60)
        if success:
            print("МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        else:
            print("МИГРАЦИЯ ЗАВЕРШЕНА С ПРЕДУПРЕЖДЕНИЯМИ")
        print("=" * 60)

        # Финальная статистика
        stats = verify_database(DATABASE_PATH)
        print(f"\nБаза данных: {DATABASE_PATH}")
        print(f"Таблицы: {', '.join(stats['tables'])}")
        print(f"Записей: users={stats['users_count']}, articles={stats['articles_count']}, "
              f"sessions={stats['sessions_count']}, interactions={stats['interactions_count']}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
