"""
Abstract interface for embedding backends.

Any embedding provider (local sentence-transformers, Gemini's embedding API,
or something else later) implements this interface so the rest of the
system never needs to know which one is in use.
"""

from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of chunk texts for storage in the vector DB."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single user question for retrieval."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension produced by this embedding model."""
        raise NotImplementedError
