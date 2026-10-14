"""User-related business logic for the sample e-commerce API."""

from datetime import datetime, timezone

from src.auth.authentication import hash_password
from src.db.connection import get_connection


class UserService:
    """Handles user creation and lookups."""

    def create_user(self, username: str, plain_password: str) -> int:
        """
        Creates a new user record with a hashed password and returns the
        new user's id. Raises sqlite3.IntegrityError if the username is
        already taken (not caught here on purpose - see the API layer).
        """
        conn = get_connection()
        password_hash = hash_password(plain_password)
        created_at = datetime.now(timezone.utc).isoformat()

        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, created_at),
        )
        conn.commit()
        return cursor.lastrowid

    def get_user_by_username(self, username: str):
        conn = get_connection()
        cursor = conn.execute(
            "SELECT id, username, created_at FROM users WHERE username = ?", (username,)
        )
        return cursor.fetchone()
