from typing import Optional, List, Dict, Any, TypedDict, Literal
from pydantic import BaseModel, Field


class FactItem(BaseModel):
    """
    Structured atomic factual claim with verified direct source attribution.
    """
    id: str = Field(description="Fact identifier, e.g. 'F1', 'F2'")
    claim: str = Field(description="Concrete factual statement or statistic")
    source_url: str = Field(description="Canonical URL of source")
    domain: str = Field(description="Domain name of source, e.g. 'techcrunch.com'")
    published_date: Optional[str] = Field(default=None, description="ISO publication date YYYY-MM-DD or null")
    evidence_quote: str = Field(description="Exact verbatim excerpt from source text")


class SourceItem(BaseModel):
    """
    Canonical normalized source article collected from live web, RSS, or HN.
    """
    title: str
    url: str
    domain: str
    published_date: Optional[str] = None
    snippet: str
    raw_content: Optional[str] = None
    source_type: str = "web"  # "tavily", "rss", "hn", "arxiv"


class DeterministicCheckResult(BaseModel):
    """
    Result of rule-based strict verification linter.
    """
    passed: bool
    missing_fact_ids: List[str] = Field(default_factory=list)
    unmatched_numbers_dates: List[str] = Field(default_factory=list)
    unauthorized_urls: List[str] = Field(default_factory=list)
    uncited_sentences: List[str] = Field(default_factory=list)
    citation_density: float = 0.0


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


class VerificationReport(BaseModel):
    """
    Comprehensive verification audit artifact stored with blog run.
    """
    score: float = Field(default=10.0, ge=0.0, le=10.0)
    passed: bool = Field(default=True)
    deterministic_passed: bool = Field(default=True)
    deterministic_failures: List[str] = Field(default_factory=list)
    detected_hallucinations: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    unverified_commands: List[str] = Field(default_factory=list)
    evaluation: Optional[Dict[str, str]] = Field(default_factory=dict, description="Multi-dimensional evaluation: completeness, readability, repetition, structure, factual_support, source_quality")
    critique: str = Field(default="PASSED - Verified factual accuracy and compelling tone.")
    status: str = Field(default="passed")  # "passed", "revising", "needs_review", "failed"


class BlogState(TypedDict):
    """
    Central shared state dictionary for the LangGraph multi-agent DAG.
    Each node transforms and returns updates to this dictionary.
    """
    topic: str
    tone: str
    target_language: str
    target_word_count: Optional[int]
    word_count: Optional[int]
    creativity: Optional[str]
    
    # Topic & Audience metadata
    target_audience: Optional[str]  # "Beginner" | "Intermediate" | "Advanced" | "Executive"
    topic_type: Optional[str]  # "trending" | "evergreen"
    category: Optional[str]    # "tech" | "ai" | "health" | "finance" | "general"
    today_date: Optional[str]  # YYYY-MM-DD
    content_plan: Optional[Dict[str, Any]]  # Structured outline, sections, code plan, FAQ plan

    # Planning & Multi-Source Collection
    planned_queries: List[str]
    query_retry_count: int
    raw_sources: List[Dict[str, Any]]
    deduped_sources: List[Dict[str, Any]]
    
    # Facts & Grounding
    facts: List[Dict[str, Any]]  # List of serialized FactItems
    research_data: Optional[str]  # Grounding text summary (backward compatibility)
    sources: List[Dict[str, Any]] # Verified sources list (backward compatibility)

    # Generated content in English (or primary output)
    title: str
    content: str
    sources_section: Optional[str]

    # Verification & Quality Audit
    verification_score: Optional[float]
    passed: Optional[bool]
    critique: Optional[str]
    detected_hallucinations: List[str]
    unverified_commands: List[str]
    verification_report: Optional[Dict[str, Any]]
    revision_count: int
    review_fallback_action: Optional[str]  # "fail" | "flag"

    # Original outputs preserved when translation occurs
    original_title: Optional[str]
    original_content: Optional[str]

    # Localized translation outputs
    translated_title: Optional[str]
    translated_content: Optional[str]

    # Diagnostic metadata & Run tracking
    current_step: str
    steps_completed: List[str]
    node_timings: Dict[str, float]
    error: Optional[str]
    run_id: Optional[str]
    idempotency_key: Optional[str]
    thread_id: Optional[str]
    user_id: Optional[int]
