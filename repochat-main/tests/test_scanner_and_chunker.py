"""
Unit tests for ingestion + chunking, run against the sample_repo fixture.

Run with:  pytest tests/
"""

import sys
from pathlib import Path

# Allow `import backend...` when running pytest from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.chunking.simple_chunker import chunk_file
from backend.ingestion.file_scanner import scan_repository

SAMPLE_REPO = Path(__file__).parent / "sample_repo"


def test_scan_repository_finds_expected_files():
    files = scan_repository(SAMPLE_REPO)
    relative_paths = {f.relative_path for f in files}

    assert "src/auth/authentication.py" in relative_paths
    assert "src/db/connection.py" in relative_paths
    assert "tests/test_auth.py" in relative_paths
    assert "README.md" in relative_paths


def test_scan_repository_ignores_hidden_and_pycache_dirs(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "module.cpython-311.pyc").write_bytes(b"\x00")
    (tmp_path / "real_module.py").write_text("def foo():\n    pass\n")

    files = scan_repository(tmp_path)
    relative_paths = {f.relative_path for f in files}

    assert "real_module.py" in relative_paths
    assert not any("pycache" in p for p in relative_paths)


def test_chunk_file_keeps_function_together():
    content = (SAMPLE_REPO / "src" / "auth" / "authentication.py").read_text()
    chunks = chunk_file(content, repo_name="sample_repo", file_path="src/auth/authentication.py", language="python")

    symbols = {c.symbol for c in chunks if c.symbol}
    assert "authenticate_user" in symbols
    assert "verify_password" in symbols
    assert "hash_password" in symbols

    auth_chunk = next(c for c in chunks if c.symbol == "authenticate_user")
    assert "def authenticate_user" in auth_chunk.content
    assert "return generate_jwt(user_id)" in auth_chunk.content


def test_chunk_file_falls_back_to_line_windows_for_unstructured_language():
    content = "\n".join(f"line {i}" for i in range(300))
    chunks = chunk_file(content, repo_name="sample_repo", file_path="data.json", language="json")

    assert len(chunks) > 1
    assert all(c.chunk_type == "block" for c in chunks)


def test_chunk_file_handles_empty_file():
    chunks = chunk_file("", repo_name="sample_repo", file_path="empty.py", language="python")
    assert chunks == []
