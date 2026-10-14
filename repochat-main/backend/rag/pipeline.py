"""
Orchestrates the Phase 1 pipeline:

  index_repository(): scan -> chunk -> embed -> store
  answer_question():  embed question -> vector search -> prompt Gemini -> grounded answer
"""

from pathlib import Path

from backend.chunking.simple_chunker import chunk_file
from backend.embeddings.factory import get_embedding_service
from backend.ingestion.file_scanner import scan_repository
from backend.llm.gemini_client import GeminiClient
from backend.rag.prompts import build_answer_prompt
from backend.vectorstore.chroma_store import ChromaVectorStore


class RagPipeline:
    def __init__(self):
        self._embedding_service = get_embedding_service()
        self._vector_store = ChromaVectorStore(self._embedding_service)
        self._llm_client: GeminiClient | None = None  # lazy: don't require a key just to index

    def _get_llm_client(self) -> GeminiClient:
        if self._llm_client is None:
            self._llm_client = GeminiClient()
        return self._llm_client

    def index_repository(self, repo_path: str, repo_name: str | None = None) -> dict:
        """
        Scans, chunks, embeds, and stores every supported file in repo_path.
        Returns a small summary dict (used by the API + UI to show
        "Files indexed: N / Chunks: M / Languages: [...]").
        """
        repo_path = str(Path(repo_path).resolve())
        repo_name = repo_name or Path(repo_path).name

        scanned_files = scan_repository(repo_path)

        total_chunks = 0
        languages_seen = set()

        for scanned_file in scanned_files:
            try:
                content = scanned_file.absolute_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            chunks = chunk_file(
                content=content,
                repo_name=repo_name,
                file_path=scanned_file.relative_path,
                language=scanned_file.language,
            )
            if not chunks:
                continue

            self._vector_store.add_chunks(chunks)
            total_chunks += len(chunks)
            languages_seen.add(scanned_file.language)

        return {
            "repo_name": repo_name,
            "repo_path": repo_path,
            "files_indexed": len(scanned_files),
            "chunks_created": total_chunks,
            "languages": sorted(languages_seen),
        }

    def answer_question(self, question: str, repo_name: str | None = None, top_k: int | None = None) -> dict:
        """
        Retrieves relevant chunks for `question` and asks Gemini to answer
        using only that context. Returns the answer text plus the raw
        matches so the API/UI can render clickable citations.
        """
        matches = self._vector_store.query(question, repo_name=repo_name, top_k=top_k)

        prompt = build_answer_prompt(question, matches)
        answer_text = self._get_llm_client().generate(prompt)

        citations = [
            {
                "file_path": m["metadata"]["file_path"],
                "start_line": m["metadata"]["start_line"],
                "end_line": m["metadata"]["end_line"],
                "symbol": m["metadata"]["symbol"] or None,
            }
            for m in matches
        ]

        return {
            "question": question,
            "answer": answer_text,
            "citations": citations,
            "retrieved_chunks": matches,
        }

    def status(self) -> dict:
        return {"total_chunks_indexed": self._vector_store.count()}
