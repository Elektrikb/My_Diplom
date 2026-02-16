# File: auth/user_db.py
import sqlite3
from typing import Dict, Optional
from passlib.context import CryptContext
from datetime import datetime
from database.db_init import get_connection, init_database, get_db_path

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        # Инициализируем БД если не существует
        init_database(self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        """Получить соединение с БД"""
        return get_connection(self.db_path)

    def get_user(self, username: str) -> Optional[dict]:
        """Получить пользователя по имени"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, hashed_password, role, created_at, is_active FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "username": row[0],
                    "hashed_password": row[1],
                    "role": row[2],
                    "created_at": row[3],
                    "is_active": bool(row[4])
                }
            return None
        finally:
            conn.close()

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Создать нового пользователя"""
        if self.get_user(username):
            return False

        hashed = pwd_context.hash(password)
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, hashed_password, role, created_at, is_active) VALUES (?, ?, ?, ?, ?)",
                (username, hashed, role, datetime.now().isoformat(), 1)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> bool:
        """Аутентификация пользователя"""
        user = self.get_user(username)
        if not user:
            return False
        # Проверка активности пользователя
        if not user.get("is_active", True):
            return False
        return pwd_context.verify(password, user["hashed_password"])

    def get_user_role(self, username: str) -> Optional[str]:
        """Получить роль пользователя"""
        user = self.get_user(username)
        if user:
            return user.get("role", "user")
        return None

    def set_user_role(self, username: str, role: str) -> bool:
        """Установить роль пользователя (admin/user)"""
        if role not in ["admin", "user"]:
            return False

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ? WHERE username = ?",
                (role, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def is_admin(self, username: str) -> bool:
        """Проверить, является ли пользователь администратором"""
        role = self.get_user_role(username)
        return role == "admin"

    def get_all_users(self) -> list:
        """Получить список всех пользователей (без паролей)"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, role, is_active, created_at FROM users"
            )
            return [
                {
                    "username": row[0],
                    "role": row[1] or "user",
                    "is_active": bool(row[2]),
                    "created_at": row[3] or ""
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def delete_user(self, username: str) -> bool:
        """Удалить пользователя"""
        user = self.get_user(username)
        if not user:
            return False

        # Защита от удаления последнего админа
        if self.is_admin(username):
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                admin_count = cursor.fetchone()[0]
                if admin_count <= 1:
                    return False
            finally:
                conn.close()

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def toggle_user_active(self, username: str) -> bool:
        """Активировать/деактивировать пользователя"""
        user = self.get_user(username)
        if not user:
            return False

        # Защита от деактивации последнего админа
        if self.is_admin(username) and user.get("is_active", True):
            conn = self._get_conn()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
                )
                active_admins = cursor.fetchone()[0]
                if active_admins <= 1:
                    return False
            finally:
                conn.close()

        new_status = 0 if user.get("is_active", True) else 1
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE username = ?",
                (new_status, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_password(self, username: str, new_password: str) -> bool:
        """Обновить пароль пользователя"""
        if not self.get_user(username):
            return False

        hashed = pwd_context.hash(new_password)
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET hashed_password = ? WHERE username = ?",
                (hashed, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @property
    def users(self) -> Dict[str, dict]:
        """Свойство для обратной совместимости - возвращает словарь всех пользователей"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, hashed_password, role, created_at, is_active FROM users"
            )
            return {
                row[0]: {
                    "username": row[0],
                    "hashed_password": row[1],
                    "role": row[2],
                    "created_at": row[3],
                    "is_active": bool(row[4])
                }
                for row in cursor.fetchall()
            }
        finally:
            conn.close()
