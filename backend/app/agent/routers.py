import logging
from backend.app.schema.state_schema import BlogState

logger = logging.getLogger(__name__)


def verification_router(state: BlogState) -> str:
    """
    Evaluates whether the blog post passes factual verification and quality standards.
    If the post failed verification (score < 8.0 or hallucinations present) and revisions < 2,
    it loops back to content_generator with targeted critique.
    
    Returns:
        'revise': if passed is False (or score < 8.0) and revision_count < 2
        'passed': if passed is True or maximum revisions reached
    """
    score = state.get("verification_score", 8.5)
    revisions = state.get("revision_count", 0)
    passed = state.get("passed", True)
    hallucinations = state.get("detected_hallucinations", [])
    
    if (not passed or (score is not None and score < 7.5) or len(hallucinations) > 0) and revisions < 2:
        logger.warning(
            f"[Verification Router] Validation FAILED (Score: {score}/10, Hallucinations: {len(hallucinations)}) -> "
            f"Routing to Content Generator for Revision #{revisions}"
        )
        return "revise"
    
    logger.info(f"[Verification Router] Validation PASSED (Score: {score}/10, Revisions: {revisions}) -> Proceeding to Language Router")
    return "passed"


def language_router(state: BlogState) -> str:
    """
    Conditional edge evaluator for multi-language workflow routing.
    
    Returns:
        'translate': when a non-English language is specified.
        'end': when the target language is English or empty.
    """
    target = state.get("target_language", "").strip().lower()
    
    if not target or target in ["english", "en", "default"]:
        logger.info("[Language Router] Target is English -> Bypassing translation -> Routing to END")
        return "end"
    
    logger.info(f"[Language Router] Target is '{target}' -> Routing to Translator Node")
    return "translate"
