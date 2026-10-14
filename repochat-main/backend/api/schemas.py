from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    repo_path: str = Field(..., description="Local filesystem path to the repository to index")
    repo_name: str | None = Field(None, description="Optional friendly name; defaults to the folder name")


class IndexResponse(BaseModel):
    repo_name: str
    repo_path: str
    files_indexed: int
    chunks_created: int
    languages: list[str]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    repo_name: str | None = Field(None, description="Restrict retrieval to a single indexed repository")
    top_k: int | None = Field(None, ge=1, le=30)


class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol: str | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]


class StatusResponse(BaseModel):
    total_chunks_indexed: int
    config_warnings: list[str]
