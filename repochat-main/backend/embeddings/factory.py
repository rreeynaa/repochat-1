"""Returns the configured EmbeddingService implementation."""

from backend.config import settings
from backend.embeddings.base import EmbeddingService

_instance: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    Returns a singleton EmbeddingService so the (potentially slow-to-load)
    local model is only loaded once per process.
    """
    global _instance
    if _instance is not None:
        return _instance

    if settings.EMBEDDING_PROVIDER == "gemini":
        from backend.embeddings.gemini_embedder import GeminiEmbedder

        _instance = GeminiEmbedder(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_EMBEDDING_MODEL,
        )
    else:
        from backend.embeddings.local_embedder import LocalEmbedder

        _instance = LocalEmbedder(model_name=settings.LOCAL_EMBEDDING_MODEL)

    return _instance
