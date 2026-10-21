import logging
from backend.app.schema.state_schema import BlogState
from backend.app.config import get_settings

logger = logging.getLogger(__name__)


def source_gate_router(state: BlogState) -> str:
    """
    Evaluates whether the clean_dedupe node satisfied the minimum-sources rule:
    - >= MIN_SOURCES_REQUIRED distinct sources (default 3)
    - >= 2 distinct domains
    
    If not met:
    - Retries plan_queries with different/broader search queries (up to 2 retries)
    - If retries exhausted: routes to fail_insufficient_sources (raising HTTP 422, zero LLM fallback)
    """
    settings = get_settings()
    min_sources = settings.MIN_SOURCES_REQUIRED
    deduped = state.get("deduped_sources", [])
    distinct_domains = {s.get("domain") for s in deduped if s.get("domain")}
    retry_count = state.get("query_retry_count", 0)
    has_error = bool(state.get("error"))

    is_sufficient = len(deduped) >= min_sources and len(distinct_domains) >= 2 and not has_error

    if is_sufficient:
        logger.info(
            f"[Source Gate Router] Ground truth SATISFIED: {len(deduped)} sources across "
            f"{len(distinct_domains)} domains. Proceeding to Fact Extraction."
        )
        return "extract_facts"

    # Retry path if under max 2 retries (0 -> retry 1, 1 -> retry 2, 2 -> exhausted)
    if retry_count < 2:
        logger.warning(
            f"[Source Gate Router] Insufficient sources ({len(deduped)} sources, {len(distinct_domains)} domains). "
            f"Triggering query replanning retry #{retry_count + 1}..."
        )
        return "plan_queries"

    logger.error(
        f"[Source Gate Router] Insufficient sources after {retry_count} retries "
        f"({len(deduped)} sources, {len(distinct_domains)} domains). Halting pipeline."
    )
    return "fail_insufficient_sources"


def verification_router(state: BlogState) -> str:
    """
    Evaluates verification outcome:
    - If passed -> routes to language check or end.
    - If failed and revision_count < 2 -> loops back to writer ('write').
    - If failed and revision_count >= 2 -> applies REVIEW_FALLBACK ('fail' or 'flag').
    """
    settings = get_settings()
    passed = state.get("passed", True)
    revisions = state.get("revision_count", 0)
    score = state.get("verification_score", 10.0)

    if passed:
        logger.info(f"[Verification Router] Article passed audit (Score: {score}/10).")
        return "passed"

    if revisions < 2:
        logger.warning(
            f"[Verification Router] Verification FAILED (Score: {score}/10, Revision #{revisions}) -> "
            f"Routing to Writer for revision..."
        )
        return "revise"

    # Max revisions reached (2 revisions completed)
    fallback = getattr(settings, "REVIEW_FALLBACK", "fail").lower().strip()
    if fallback == "flag":
        logger.warning(
            f"[Verification Router] Max revisions reached. Flagging article with status 'needs_review'."
        )
        return "flag_review"
    else:
        logger.error(
            f"[Verification Router] Max revisions reached (Score: {score}/10). Halting pipeline with failure."
        )
        return "fail_verification"


def language_router(state: BlogState) -> str:
    """
    Conditional edge evaluator for multi-language workflow routing.
    """
    target = state.get("target_language", "").strip().lower()
    
    if not target or target in ["english", "en", "default"]:
        logger.info("[Language Router] Target is English -> Bypassing translation -> Routing to END")
        return "end"
    
    logger.info(f"[Language Router] Target is '{target}' -> Routing to Translator Node")
    return "translate"
