"""
Thin wrapper around a persistent ChromaDB collection.

Persisting locally (instead of in-memory) means the repository doesn't need
to be re-embedded every time the application restarts.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.chunking.simple_chunker import CodeChunk
from backend.config import settings
from backend.embeddings.base import EmbeddingService


class ChromaVectorStore:
    def __init__(self, embedding_service: EmbeddingService, persist_dir: str | None = None):
        self._embedding_service = embedding_service
        self._client = chromadb.PersistentClient(
            path=persist_dir or settings.VECTOR_DB_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # One collection per whole system for Phase 1; repo_name is stored
        # as metadata so results can be filtered per-repository.
        self._collection = self._client.get_or_create_collection(
            name="code_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[CodeChunk]) -> None:
        if not chunks:
            return

        texts = [self._format_for_embedding(c) for c in chunks]
        embeddings = self._embedding_service.embed_documents(texts)

        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.content for c in chunks],
            metadatas=[
                {
                    "repo_name": c.repo_name,
                    "file_path": c.file_path,
                    "language": c.language,
                    "symbol": c.symbol or "",
                    "chunk_type": c.chunk_type,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "imports": ", ".join(c.imports),
                }
                for c in chunks
            ],
        )

    def delete_by_file(self, repo_name: str, file_path: str) -> None:
        """Removes all chunks for a given file (used before re-indexing it)."""
        self._collection.delete(where={"$and": [{"repo_name": repo_name}, {"file_path": file_path}]})

    def query(self, question: str, repo_name: str | None = None, top_k: int | None = None) -> list[dict]:
        total = self._collection.count()
        if total == 0:
            return []
        query_embedding = self._embedding_service.embed_query(question)
        where = {"repo_name": repo_name} if repo_name else None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k or settings.TOP_K_RESULTS, total),
            where=where,
        )

        matches = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i in range(len(ids)):
            matches.append(
                {
                    "chunk_id": ids[i],
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                }
            )
        return matches

    def count(self) -> int:
        return self._collection.count()

    @staticmethod
    def _format_for_embedding(chunk: CodeChunk) -> str:
        """
        Prefixes the chunk with light metadata before embedding, so the
        embedding model has a chance to pick up on the file/symbol context,
        not just the raw code.
        """
        header = f"# file: {chunk.file_path}"
        if chunk.symbol:
            header += f" | symbol: {chunk.symbol}"
        header += f" | language: {chunk.language}"
        return f"{header}\n{chunk.content}"
