
![version](https://img.shields.io/badge/version-v0.4-blue) ![status](https://img.shields.io/badge/status-active%20development-yellow)

# repochat - codebase intelligence system

a rag based tool that lets you ask natural-language questions about a software repository and get answers grounded in the actual code, with file and line citations.

built to run on a laptop with **8GB RAM and no GPU**, using **Gemini API** for LLM inference and local embeddings for retrieval.

---

## features

* repository indexing
* structure-aware code chunking
* local code embeddings with `all-MiniLM-L6-v2`
* persistent vector storage with ChromaDB
* semantic code search
* gemini-powered answers
* file and line-level citations
* supports python, javascript, typescript, java, go, c/c++ and rust

---

## architecture

```text
repository
     │
     ▼
file scanner
     │
     ▼
code chunker
     │
     ▼
local embeddings
     │
     ▼
chromaDB
     │
     ▼
vector search
     │
     ▼
gemini
     │
     ▼
answer + citations
```

---

## tech stack

| component       | technology            |
| --------------- | --------------------- |
| backend         | fastAPI               |
| frontend        | streamlit             |
| LLM             | gemini api            |
| embeddings      | sentence transformers |
| vector database | chromaDB              |
| language        | python                |

---

## project structure

```text
codebase-intelligence/
├── backend/
│   ├── api/
│   ├── ingestion/
│   ├── chunking/
│   ├── embeddings/
│   ├── vectorstore/
│   ├── llm/
│   ├── rag/
│   ├── config.py
│   └── main.py
├── frontend/
│   └── app.py
├── data/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── run.py
```

---

## setup

### 1. clone the repository

```bash
git clone "https://github.com/rreeynaa/repochat"
cd repochat
```

### 2. create a virtual environment

**windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. install dependencies

```bash
pip install -r requirements.txt
```

### 4. configure gemini

Create an API key from [Google AI Studio](https://aistudio.google.com/apikey).

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## run

start the backend:

```bash
python run.py
```

start the frontend in another terminal:

```bash
streamlit run frontend/app.py
```

open the streamlit interface and enter the path of the repository you want to analyze.

---


## current scope —> phase 1

phase 1 focuses on the core RAG pipeline:

* vector-based retrieval
* heuristic structural chunking
* local embeddings
* chromaDB storage
* gemini-based generation
* code citations

### limitations

* no hybrid BM25 + vector retrieval
* no dependency graph
* no impact analysis
* no incremental indexing
* no Git awareness

---

## roadmap

### phase 2

* tree-sitter based code parsing
* hybrid BM25 + vector retrieval
* improved citations
* better code metadata

### phase 3

* dependency graph
* function and class relationships
* impact analysis

### phase 4

* incremental indexing
* file hashing
* git-aware retrieval

### phase 5

* automated evaluation
* recall@5
* citation accuracy
* latency benchmarking

