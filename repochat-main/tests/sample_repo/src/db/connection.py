"""Database connection utilities for the sample e-commerce API."""

import sqlite3

DATABASE_PATH = "app.db"

_connection = None


def get_connection():
    """
    Returns a shared SQLite connection, creating it on first use.

    BUG (intentional, for testing): this does not handle the case where the
    database file is locked or missing permissions - sqlite3.connect() will
    raise an unhandled exception that propagates straight to the caller.
    """
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    return _connection


def init_db():
    """Creates the tables used by the application if they don't exist yet."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_cents INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
