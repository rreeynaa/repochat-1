"""
Prompt templates for the RAG pipeline.

The core requirement here (per project spec) is that Gemini treats the
retrieved code as the ONLY source of truth, never invents files/functions,
explicitly says when it can't answer from what was retrieved, and always
cites file paths + line ranges.
"""

SYSTEM_INSTRUCTIONS = """You are a codebase intelligence assistant. You answer questions about a \
specific software repository using ONLY the code chunks provided to you below as context.

Strict rules you must follow:
1. Use the provided repository context as your primary and only source of truth about this codebase.
2. Do NOT invent functions, classes, files, or behavior that are not present in the context below.
3. If the retrieved context does not contain enough information to answer confidently, say so \
explicitly instead of guessing (e.g. "The retrieved code does not show how X is implemented").
4. Clearly separate facts you found in the repository from general programming knowledge or \
suggestions. Label general suggestions as such.
5. Every claim about the codebase must be backed by a citation in the exact format `file_path:start_line-end_line`, \
taken directly from the context below. Do not fabricate line numbers.
6. Do not claim a chunk contains something it does not. Quote or paraphrase only what is actually there.
7. Keep the answer focused and avoid repeating the full code back verbatim; summarize what it does.
"""


def build_answer_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    context_blocks = []
    for match in retrieved_chunks:
        meta = match["metadata"]
        citation = f"{meta['file_path']}:{meta['start_line']}-{meta['end_line']}"
        symbol_info = f" (symbol: {meta['symbol']})" if meta.get("symbol") else ""
        context_blocks.append(
            f"--- Chunk [{citation}]{symbol_info}, language={meta['language']} ---\n"
            f"{match['content']}\n"
        )

    context_text = "\n".join(context_blocks) if context_blocks else "(No relevant chunks were retrieved.)"

    return f"""{SYSTEM_INSTRUCTIONS}

# Retrieved repository context

{context_text}

# User question

{question}

# Your answer
Answer the question above using only the context provided. Include citations in the \
format `file_path:start_line-end_line` for every specific claim about the codebase. \
End your answer with a "Relevant files" list of the distinct file paths you referenced.
"""
