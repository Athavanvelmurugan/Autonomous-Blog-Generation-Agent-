from typing import Optional, List, Dict, Any, TypedDict
from pydantic import BaseModel, Field


class VerifierEvaluation(BaseModel):
    """
    Structured fact-checking evaluation schema for the verifier agent.
    Guarantees deterministic, type-safe scoring without brittle regex parsing.
    """
    score: float = Field(ge=0.0, le=10.0, description="Factuality score out of 10.0")
    passed: bool = Field(description="True if score >= 8.0 and zero critical hallucinations")
    detected_hallucinations: List[str] = Field(
        default_factory=list,
        description="Specific fabricated commands, fake flags, non-existent URLs, or wrong architecture claims"
    )
    unverified_commands: List[str] = Field(
        default_factory=list,
        description="Shell or CLI commands present in draft but missing from reference documentation"
    )
    critique: str = Field(description="Actionable editorial critique directing the writer on what to eliminate")


class BlogState(TypedDict):
    """
    Central shared state dictionary for the LangGraph multi-agent DAG.
    Each node transforms and returns updates to this dictionary.
    """
    topic: str
    tone: str
    target_language: str
    creativity: Optional[str]
    
    # Real-Time Web Research Context & Citations
    research_data: Optional[str]
    sources: List[Dict[str, Any]]

    # Generated content in English (or primary output)
    title: str
    content: str

    # Verification & Fact-Checking Audit
    verification_score: Optional[float]
    passed: Optional[bool]
    critique: Optional[str]
    detected_hallucinations: List[str]
    unverified_commands: List[str]
    revision_count: int

    # Original outputs preserved when translation occurs
    original_title: Optional[str]
    original_content: Optional[str]

    # Localized translation outputs
    translated_title: Optional[str]
    translated_content: Optional[str]

    # Diagnostic metadata & Run tracking
    current_step: str
    steps_completed: List[str]
    error: Optional[str]
    run_id: Optional[str]
    idempotency_key: Optional[str]
    thread_id: Optional[str]
    user_id: Optional[int]

