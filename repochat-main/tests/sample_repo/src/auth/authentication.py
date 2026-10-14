"""Authentication logic for the sample e-commerce API."""

import hashlib
import time

from src.db.connection import get_connection

JWT_SECRET = "change-me-in-production"


def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using SHA-256 with no salt.

    BUG (intentional, for testing): no per-user salt is used, which makes
    this vulnerable to rainbow-table attacks. Kept simple on purpose so the
    RAG system's "find potential bugs" feature has something real to find.
    """
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Checks whether a plaintext password matches a stored hash."""
    return hash_password(plain_password) == password_hash


def generate_jwt(user_id: int) -> str:
    """Generates a (deliberately simplified) JWT-like token for a user."""
    payload = f"{user_id}:{int(time.time()) + 3600}"
    signature = hashlib.sha256((payload + JWT_SECRET).encode("utf-8")).hexdigest()
    return f"{payload}.{signature}"


def authenticate_user(username: str, plain_password: str) -> str | None:
    """
    Verifies a username/password pair against the database and returns a
    JWT token on success, or None if authentication fails.
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()
    if row is None:
        return None

    user_id, password_hash = row
    if not verify_password(plain_password, password_hash):
        return None

    return generate_jwt(user_id)
