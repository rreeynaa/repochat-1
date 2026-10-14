"""
Splits source files into meaningful chunks for embedding.

Phase 1 approach (deliberately simple, upgraded to real AST/tree-sitter in
Phase 2):
  - For Python, JavaScript, TypeScript, Java, Go, C/C++, Rust: use indentation
    / brace-depth heuristics to detect top-level function and class
    boundaries, so "def create_user(...):" and its body stay together as one
    chunk instead of being cut at an arbitrary character count.
  - For everything else (HTML, CSS, SQL, JSON, YAML, Markdown, and any file
    where the heuristic finds no structure): fall back to fixed-size,
    overlapping line windows.

Every chunk carries metadata: file path, language, symbol name (if known),
start/end line, and chunk type.
"""

import hashlib
import re
from dataclasses import dataclass, field

from backend.config import settings

# Languages we attempt structural (function/class) splitting for.
STRUCTURED_LANGUAGES = {
    "python", "javascript", "typescript", "java", "go", "c", "cpp", "rust",
}

# Regexes that spot the START of a top-level function or class/struct
# definition for each language family. This is intentionally forgiving
# (recall over precision) since a missed boundary just falls through to the
# line-based fallback for that region, which is still a reasonable chunk.
DEFINITION_PATTERNS = {
    "python": re.compile(r"^(\s*)(def|class)\s+(\w+)"),
    "javascript": re.compile(
        r"^(\s*)(?:export\s+)?(?:default\s+)?"
        r"(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|"
        r"const\s+(\w+)\s*=\s*(?:async\s*)?\(.*\)\s*=>)"
    ),
    "typescript": re.compile(
        r"^(\s*)(?:export\s+)?(?:default\s+)?"
        r"(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|interface\s+(\w+)|"
        r"const\s+(\w+)\s*=\s*(?:async\s*)?\(.*\)\s*=>)"
    ),
    "java": re.compile(
        r"^(\s*)(?:public|private|protected|static|\s)*"
        r"(?:class|interface|enum)\s+(\w+)|"
        r"^(\s*)(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+(\w+)\s*\("
    ),
    "go": re.compile(r"^(\s*)func\s+(?:\(\w+ \*?\w+\)\s+)?(\w+)"),
    "c": re.compile(r"^(\s*)[\w\*\s]+\s(\w+)\s*\([^;]*\)\s*\{?\s*$"),
    "cpp": re.compile(r"^(\s*)[\w:<>\*\s]+\s(\w+)\s*\([^;]*\)\s*\{?\s*$"),
    "rust": re.compile(r"^(\s*)(?:pub\s+)?(?:async\s+)?fn\s+(\w+)|^(\s*)(?:pub\s+)?struct\s+(\w+)"),
}


@dataclass
class CodeChunk:
    chunk_id: str
    repo_name: str
    file_path: str  # relative to repo root
    language: str
    symbol: str | None
    chunk_type: str  # "function" | "class" | "block" | "file"
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    content: str
    imports: list[str] = field(default_factory=list)


_KEYWORDS_TO_SKIP = {
    "def", "class", "function", "interface", "struct", "fn", "enum",
    "pub", "async", "static", "final", "public", "private", "protected",
    "const", "export", "default",
}


def _extract_symbol_name(match: re.Match) -> str | None:
    # Several groups may match keywords (e.g. "def", "class", "public") as a
    # side effect of how the pattern is written; walk every group and take
    # the last one that looks like a real identifier and isn't a keyword,
    # since the symbol name capture group is typically the last to match.
    candidate = None
    for group in match.groups():
        if not group:
            continue
        if re.fullmatch(r"\w+", group) and group not in _KEYWORDS_TO_SKIP:
            candidate = group
    return candidate


def _make_chunk_id(repo_name: str, file_path: str, start_line: int, end_line: int) -> str:
    raw = f"{repo_name}:{file_path}:{start_line}-{end_line}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _extract_imports(lines: list[str], language: str) -> list[str]:
    imports = []
    import_prefixes = {
        "python": ("import ", "from "),
        "javascript": ("import ", "require("),
        "typescript": ("import ", "require("),
        "java": ("import ",),
        "go": ("import ",),
        "rust": ("use ",),
        "c": ("#include",),
        "cpp": ("#include",),
    }
    prefixes = import_prefixes.get(language, ())
    for line in lines[:50]:  # imports are almost always near the top
        stripped = line.strip()
        if any(stripped.startswith(p) for p in prefixes):
            imports.append(stripped)
    return imports


def _line_window_fallback(
    lines: list[str], repo_name: str, file_path: str, language: str
) -> list[CodeChunk]:
    """Fixed-size overlapping windows, used when no structure is detected."""
    max_lines = settings.MAX_CHUNK_LINES
    overlap = settings.CHUNK_OVERLAP_LINES
    total = len(lines)
    chunks = []

    if total == 0:
        return chunks

    start = 0
    while start < total:
        end = min(start + max_lines, total)
        content = "\n".join(lines[start:end])
        if content.strip():
            chunks.append(
                CodeChunk(
                    chunk_id=_make_chunk_id(repo_name, file_path, start + 1, end),
                    repo_name=repo_name,
                    file_path=file_path,
                    language=language,
                    symbol=None,
                    chunk_type="block",
                    start_line=start + 1,
                    end_line=end,
                    content=content,
                    imports=_extract_imports(lines, language),
                )
            )
        if end == total:
            break
        start = end - overlap  # step forward, keeping a little overlap for context

    return chunks


def _structural_chunk(
    lines: list[str], repo_name: str, file_path: str, language: str
) -> list[CodeChunk] | None:
    """
    Attempts to split by top-level function/class definitions using
    indentation as a proxy for scope. Returns None if no definitions were
    found at all (caller should fall back to line windows).
    """
    pattern = DEFINITION_PATTERNS.get(language)
    if pattern is None:
        return None

    # Find line indices where a definition starts, along with symbol name
    # and the indentation level of that definition (used to find where the
    # block ends: the next line at the same-or-lower indentation).
    boundaries: list[tuple[int, str | None, int]] = []
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            indent = len(line) - len(line.lstrip())
            symbol = _extract_symbol_name(match)
            boundaries.append((i, symbol, indent))

    if not boundaries:
        return None

    imports = _extract_imports(lines, language)
    chunks: list[CodeChunk] = []
    max_lines = settings.MAX_CHUNK_LINES

    for idx, (start_idx, symbol, indent) in enumerate(boundaries):
        # Find where this definition's block ends: the next line, after
        # start_idx, that is non-blank and indented <= this definition's
        # indent (i.e. we've returned to the same or a shallower scope).
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            candidate = lines[j]
            if not candidate.strip():
                continue
            candidate_indent = len(candidate) - len(candidate.lstrip())
            if candidate_indent <= indent and j != start_idx:
                # Also make sure we're not stopping in the middle of another
                # boundary that starts later at a deeper indent by mistake;
                # this simple rule is a reasonable Phase-1 approximation.
                end_idx = j
                break

        # Cap extremely long blocks so a single giant class doesn't become
        # one unwieldy, low-precision chunk.
        capped_end_idx = min(end_idx, start_idx + max_lines)

        content = "\n".join(lines[start_idx:capped_end_idx]).rstrip()
        if not content.strip():
            continue

        chunk_type = "class" if re.search(r"\bclass\b|\binterface\b|\bstruct\b", lines[start_idx]) else "function"

        chunks.append(
            CodeChunk(
                chunk_id=_make_chunk_id(repo_name, file_path, start_idx + 1, capped_end_idx),
                repo_name=repo_name,
                file_path=file_path,
                language=language,
                symbol=symbol,
                chunk_type=chunk_type,
                start_line=start_idx + 1,
                end_line=capped_end_idx,
                content=content,
                imports=imports,
            )
        )

    # Also capture the "preamble" (imports, module-level constants, etc.)
    # before the first definition, if it's non-trivial.
    first_def_line = boundaries[0][0]
    if first_def_line > 0:
        preamble = "\n".join(lines[:first_def_line]).strip()
        if preamble:
            chunks.insert(
                0,
                CodeChunk(
                    chunk_id=_make_chunk_id(repo_name, file_path, 1, first_def_line),
                    repo_name=repo_name,
                    file_path=file_path,
                    language=language,
                    symbol=None,
                    chunk_type="block",
                    start_line=1,
                    end_line=first_def_line,
                    content=preamble,
                    imports=imports,
                ),
            )

    return chunks


def chunk_file(content: str, repo_name: str, file_path: str, language: str) -> list[CodeChunk]:
    """
    Main entry point: turns a file's raw text into a list of CodeChunks.
    """
    lines = content.splitlines()
    if not lines:
        return []

    if language in STRUCTURED_LANGUAGES:
        structural = _structural_chunk(lines, repo_name, file_path, language)
        if structural:
            return structural

    return _line_window_fallback(lines, repo_name, file_path, language)
