from typing import Optional, List, Dict, Literal , Any
from pydantic import BaseModel, Field 


class BlogGenerationRequest(BaseModel):
    topic: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="The subject or theme for the blog post",
        examples=["Autonomous Agentic AI in 2026", "Mastering FastAPI with PostgreSQL"]
    )
    tone: Optional[str] = Field(
        "Informative",
        description="Writing tone: Informative, Technical, Casual, or Executive",
        examples=["Technical"]
    )
    target_language: Optional[str] = Field(
        "English",
        description="Target output language for the blog",
        examples=["English", "Spanish", "French", "German", "Hindi", "Japanese"]
    )
    creativity: Optional[Literal["low", "balanced", "high"]] = Field(
        "balanced",
        description="Creativity level for writing nodes: low, balanced, or high",
        examples=["balanced"]
    )
    idempotency_key: Optional[str] = Field(
        None,
        description="Unique request key to guarantee idempotent execution and avoid duplicate agent runs"
    )
    api_key: Optional[str] = Field(
        None,
        description="Optional API key for authenticated multi-tenant isolation"
    )


class BlogGenerationResponse(BaseModel):
    id: Optional[int] = Field(None, description="Database record ID if stored in PostgreSQL")
    status: str = Field("success", description="Status string: success or error")
    topic: str
    tone: str
    language: str
    title: str
    content: str
    verification_score: Optional[float] = Field(8.5, description="Fact check and quality score out of 10")
    critique: Optional[str] = Field(None, description="Editorial review feedback")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Citations and live sources retrieved")
    original_title: Optional[str] = None
    original_content: Optional[str] = None
    execution_time_seconds: float
    steps_completed: List[str]
    error: Optional[str] = None


class BlogPostSummary(BaseModel):
    id: int
    topic: str
    tone: str
    target_language: str
    title: str
    content: str
    verification_score: Optional[float] = 8.5
    critique: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    original_title: Optional[str] = None
    original_content: Optional[str] = None
    execution_time_seconds: float
    created_at: Optional[str] = None


class LanguageOption(BaseModel):
    code: str
    name: str
    native_name: str


class BlogPostUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ReaderEventCreateRequest(BaseModel):
    event_type: str = Field(..., description="view, scroll, copy, download_pdf, share")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
