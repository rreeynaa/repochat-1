"""
Local embedding backend using sentence-transformers.

This is the default for the whole project because:
  - It runs entirely on CPU and fits comfortably in 8GB of RAM
    (all-MiniLM-L6-v2 is ~90MB and produces 384-dim vectors).
  - It doesn't touch the Gemini free-tier quota at all, which matters a lot
    here: indexing a repository means embedding potentially thousands of
    chunks, while Gemini's embedding free tier is limited to well under a
    thousand requests/day. Reserving Gemini calls for answer generation
    (one call per user question) is a much better use of that quota.
  - It requires no network access after the model is first downloaded, so
    re-indexing works offline.
"""

from sentence_transformers import SentenceTransformer

from backend.embeddings.base import EmbeddingService


class LocalEmbedder(EmbeddingService):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Loaded once and reused; loading the model is the slow part
        # (a few seconds), embedding calls themselves are fast.
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        embedding = self._model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension
