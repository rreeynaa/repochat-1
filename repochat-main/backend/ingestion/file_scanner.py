"""
Walks a repository directory and returns the source files worth indexing.

Responsibilities:
  - skip junk directories (.git, node_modules, __pycache__, virtualenvs, build output...)
  - skip hidden directories, binary files, lockfiles, minified bundles, and huge files
  - map each file's extension to a language name (the same names the chunker
    uses: "python", "javascript", "typescript", "java", "go", "c", "cpp", "rust",
    plus "markdown", "json", "yaml", "html", "css", "sql", ... for line-window chunking)

Public API:
    scan_repository(repo_path) -> list[ScannedFile]
"""

import os
from dataclasses import dataclass
from pathlib import Path

# extension (lowercase, with dot) -> language name
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".rs": "rust",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".sql": "sql",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".rst": "text",
    ".txt": "text",
    ".sh": "shell",
}

# Directory names that are never worth indexing.
IGNORED_DIRS: set[str] = {
    "node_modules", "__pycache__", "venv", "env", "build", "dist", "target",
    "site-packages", "vendor", "coverage", "htmlcov", "out", "bin", "obj",
}

# Specific filenames that are generated / noisy.
IGNORED_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Pipfile.lock", "Cargo.lock", "go.sum",
}

# Skip files larger than this (generated data, bundles, dumps).
MAX_FILE_SIZE_BYTES = 1_000_000  # 1 MB


@dataclass
class ScannedFile:
    absolute_path: Path
    relative_path: str  # POSIX-style ("src/auth/authentication.py"), relative to repo root
    language: str
    size_bytes: int


def _is_binary(path: Path) -> bool:
    """Cheap binary check: a NUL byte in the first 2 KB."""
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(2048)
    except OSError:
        return True


def scan_repository(repo_path: str | Path) -> list[ScannedFile]:
    """
    Returns every supported, non-ignored text file under repo_path, sorted by
    relative path. Raises FileNotFoundError / NotADirectoryError for bad input
    (the API layer turns those into HTTP 400).
    """
    root = Path(repo_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {root}")

    results: list[ScannedFile] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune in place so os.walk doesn't descend into ignored/hidden dirs.
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".")
            and d not in IGNORED_DIRS
            and not d.endswith(".egg-info")
        )

        for filename in sorted(filenames):
            if filename.startswith(".") or filename in IGNORED_FILES:
                continue
            if filename.endswith((".min.js", ".min.css")):
                continue

            path = Path(dirpath) / filename
            language = EXTENSION_TO_LANGUAGE.get(path.suffix.lower())
            if language is None:
                continue

            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size == 0 or size > MAX_FILE_SIZE_BYTES:
                continue
            if _is_binary(path):
                continue

            results.append(
                ScannedFile(
                    absolute_path=path,
                    relative_path=path.relative_to(root).as_posix(),
                    language=language,
                    size_bytes=size,
                )
            )

    results.sort(key=lambda f: f.relative_path)
    return results
