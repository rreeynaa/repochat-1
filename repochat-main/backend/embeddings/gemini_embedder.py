"""
Gemini embedding API backend.

An alternative to LocalEmbedder, kept behind the same EmbeddingService
interface. Not the default because Gemini's free-tier embedding quota
(tens of requests/minute, under a thousand/day) is easy to exhaust while
indexing even a medium-sized repository. Use this only if you specifically
want Gemini's embedding quality and are willing to manage that quota
(e.g. by indexing incrementally, see Phase 4) or are on a paid plan.
"""

from google import genai
from google.genai import types

from backend.embeddings.base import EmbeddingService


class GeminiEmbedder(EmbeddingService):
    # gemini-embedding-001 supports 128-3072 dims; 768 is a good balance of
    # quality vs. storage/RAM for a local vector DB.
    _OUTPUT_DIMENSION = 768

    def __init__(self, api_key: str, model_name: str = "gemini-embedding-001"):
        if not api_key:
            raise ValueError("Gemini API key is required to use GeminiEmbedder.")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        # The Gemini embed_content endpoint accepts one input per call in
        # some SDK versions; we loop defensively rather than assume batch
        # support, since batch limits change between free/paid tiers.
        results = []
        for text in texts:
            response = self._client.models.embed_content(
                model=self._model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._OUTPUT_DIMENSION,
                ),
            )
            results.append(response.embeddings[0].values)
        return results

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text], task_type="RETRIEVAL_QUERY")[0]

    @property
    def dimension(self) -> int:
        return self._OUTPUT_DIMENSION
