from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings

app = FastAPI(
    title="Codebase Intelligence System",
    description="RAG-based Q&A over a source code repository, grounded in the actual code.",
    version="0.1.0-phase1",
)

# Permissive CORS: this is a local developer tool (Streamlit frontend on
# localhost), not a public-facing service.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Codebase Intelligence System",
        "phase": "1 - Basic RAG",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
