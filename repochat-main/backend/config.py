"""
Central configuration for the Codebase Intelligence System.

Everything that could vary between machines or that is a secret lives here,
loaded from environment variables (via a .env file in development).

IMPORTANT: The Gemini API key is NEVER hardcoded. It is only ever read from
the GEMINI_API_KEY environment variable.
"""

import os

# Silence ChromaDB's telemetry (its posthog client logs harmless errors on some versions).
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a .env file in the project root, if present.
# This does NOT overwrite variables that are already set in the real
# environment (e.g. in production you might set them via the OS instead).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


class Settings:
    # --- Gemini ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # --- Embeddings ---
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")  # "local" | "gemini"
    LOCAL_EMBEDDING_MODEL: str = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # --- Storage ---
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./data/cache")

    # --- Chunking ---
    MAX_CHUNK_LINES: int = _get_int("MAX_CHUNK_LINES", 120)
    CHUNK_OVERLAP_LINES: int = _get_int("CHUNK_OVERLAP_LINES", 10)

    # --- Retrieval ---
    TOP_K_RESULTS: int = _get_int("TOP_K_RESULTS", 8)

    # --- Server ---
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = _get_int("API_PORT", 8000)

    def validate(self) -> list[str]:
        """Return a list of human-readable problems with the current config."""
        problems = []
        if not self.GEMINI_API_KEY:
            problems.append(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://aistudio.google.com/apikey"
            )
        if self.EMBEDDING_PROVIDER not in ("local", "gemini"):
            problems.append(
                f"EMBEDDING_PROVIDER must be 'local' or 'gemini', got '{self.EMBEDDING_PROVIDER}'"
            )
        return problems


settings = Settings()

# Make sure storage folders exist so ChromaDB never fails on a missing path.
for _d in (settings.VECTOR_DB_DIR, settings.CACHE_DIR):
    Path(_d).mkdir(parents=True, exist_ok=True)
