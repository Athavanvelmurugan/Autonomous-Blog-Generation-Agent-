import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.schema.state_schema import DeterministicCheckResult, VerificationReport
from backend.app.core.llm import get_llm
from backend.app.core.groq_guard import safe_llm_invoke
from backend.app.config import get_settings

logger = logging.getLogger(__name__)

SEMANTIC_VERIFIER_SYSTEM_PROMPT = """You are an uncompromising editorial fact-checking auditor.
Your job is to rigorously evaluate a blog draft against the provided Verified Facts Table.

EVALUATION CRITERIA:
1. Grounding: Does the draft strictly reflect the claims in the Facts Table?
2. Hallucinations: Flag any claims, metrics, or announcements that do NOT appear in the facts.
3. Anti-Hedging: Flag parenthetical excuses (e.g. '(syntax may vary)', '(if not documented)').
4. Banned Clichés: Flag robotic tropes like 'delve into', 'testament to', 'beacon of', 'game-changer'.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object adhering strictly to this schema:
{
  "score": <float between 0.0 and 10.0>,
  "passed": <boolean: true if score >= 8.0 and zero critical hallucinations>,
  "detected_hallucinations": ["list of unsupported claims"],
  "unsupported_claims": ["list of specific statements lacking fact grounding"],
  "critique": "Actionable feedback directing the writer on what to eliminate or revise"
}
"""


def run_deterministic_checks(
    draft_content: str,
    facts: List[Dict[str, Any]],
    allowed_urls: List[str],
    sources: Optional[List[Dict[str, Any]]] = None
) -> DeterministicCheckResult:
    """
    Executes fast, deterministic programmatic checks:
    1. Cited fact IDs must exist in the facts list.
    2. Every significant number/date/percentage/version in the draft must appear in the facts or sources.
    3. No raw URLs outside the allowed source URL list.
    4. Sentence-level claims must include citations.
    """
    known_fact_ids = {f["id"].upper(): f for f in facts}
    
    sources_corpus = ""
    if sources:
        sources_corpus = " ".join([
            f"{s.get('title', '')} {s.get('url', '')} {s.get('raw_content', '')[:1000]} {s.get('snippet', '')}"
            for s in sources
        ])

    # Include title line in corpus so topic metrics (e.g. 'Python 3.13') are recognized
    title_line = draft_content.split("\n")[0] if draft_content else ""
    facts_text_corpus = (" ".join([
        f"{f.get('claim', '')} {f.get('evidence_quote', '')} {f.get('published_date', '')} {f.get('source_url', '')}"
        for f in facts
    ]) + " " + sources_corpus + " " + title_line).lower()

    missing_fact_ids: List[str] = []
    unmatched_numbers: List[str] = []
    unauthorized_urls: List[str] = []
    uncited_paragraphs: List[str] = []

    # 1. Cited Fact IDs Check (supports both raw [F1] and post-processed [[F1: domain]](url))
    cited_ids = re.findall(r"\[(?:\[)?(F\d+)(?::[^\]]+)?\]", draft_content, re.IGNORECASE)
    for cid in cited_ids:
        if cid.upper() not in known_fact_ids:
            missing_fact_ids.append(f"Unknown cited fact ID: [{cid}]")

    # 2. Unauthorized Raw URLs Check (Writer should not output raw URLs outside allowed sources)
    # Strip approved citation links [[F1: ...]] and Sources appendix first
    body_no_citations = re.sub(r"\[+[^\]]+\]+\([^\)]+\)", "", draft_content)
    body_no_citations = re.split(r"(?i)\n##\s*sources", body_no_citations)[0]
    raw_urls = re.findall(r"https?://[^\s\>\)\]]+", body_no_citations)
    normalized_allowed = [u.rstrip("/").lower() for u in allowed_urls]
    for u in raw_urls:
        clean_u = u.rstrip("/").lower()
        if clean_u not in normalized_allowed:
            unauthorized_urls.append(f"Unauthorized or unverified raw URL in draft: {u}")

    # 3. Number / Date / Metric / Version Check
    # Strip markdown code blocks, URLs, and the trailing Sources appendix before checking prose numbers
    prose_clean = re.sub(r"```.*?```", "", draft_content, flags=re.DOTALL)
    prose_clean = re.split(r"(?i)\n##\s*sources", prose_clean)[0]
    # Strip all markdown links: [text](url) and [[text]](url)
    prose_clean = re.sub(r"\[+[^\]]+\]+\([^\)]*\)", "", prose_clean)
    # Strip standalone URLs
    prose_clean = re.sub(r"https?://\S+", "", prose_clean)
    # Strip citation brackets like [[F1: ...]] or [F1] so ID numbers are not extracted
    prose_clean = re.sub(r"\[+F\d+[^\]]*\]+", "", prose_clean)

    extracted_metrics = re.findall(r"\b(?:\$?\d+(?:\.\d+)?(?:%|M|B|k|x|th|st|nd|rd)?|\bv\d+(?:\.\d+)*)\b", prose_clean)
    for metric in set(extracted_metrics):
        m_clean = metric.strip().lower()
        if m_clean in ["1", "2", "3", "4", "5", "10", "0", "h2", "h3"]:
            continue
        if m_clean not in facts_text_corpus:
            unmatched_numbers.append(metric)

    # 4. Sentence / Paragraph Level Citation Check
    # Check paragraphs from draft_content (excluding ## Sources) before citations were stripped
    raw_body = re.split(r"(?i)\n##\s*sources", draft_content)[0]
    paragraphs = [p.strip() for p in raw_body.split("\n\n") if p.strip()]
    
    factual_paras = 0
    cited_paras = 0

    for p in paragraphs:
        if p.startswith("#") or p.startswith(">") or len(p.split()) < 15:
            continue
        factual_paras += 1
        # Match both raw [F1] and post-processed [[F1: domain]](url)
        if re.search(r"\[\[?F\d+", p, re.IGNORECASE):
            cited_paras += 1
        else:
            snippet = p[:80] + "..." if len(p) > 80 else p
            uncited_paragraphs.append(snippet)

    citation_density = round(cited_paras / max(factual_paras, 1), 2)
    has_sufficient_citations = (factual_paras == 0 or cited_paras >= max(1, int(factual_paras * 0.5)))

    passed = (
        len(missing_fact_ids) == 0 and
        len(unauthorized_urls) == 0 and
        len(unmatched_numbers) <= 1 and  # Allow max 1 minor format variation
        has_sufficient_citations
    )

    return DeterministicCheckResult(
        passed=passed,
        missing_fact_ids=missing_fact_ids,
        unmatched_numbers_dates=unmatched_numbers,
        unauthorized_urls=unauthorized_urls,
        uncited_sentences=uncited_paragraphs[:3],
        citation_density=citation_density
    )


async def run_full_verification(
    draft_content: str,
    facts: List[Dict[str, Any]],
    sources: List[Dict[str, Any]]
) -> VerificationReport:
    """
    Executes two-stage verification:
    Stage 1: Deterministic rule-based checks.
    Stage 2: LLM semantic evaluation at temperature 0.0 with optional VERIFIER_MODEL.
    """
    settings = get_settings()
    allowed_urls = [s.get("url", "") for s in sources if s.get("url")]

    # Stage 1: Deterministic checks
    det_result = run_deterministic_checks(draft_content, facts, allowed_urls, sources=sources)
    
    det_failures = []
    if det_result.missing_fact_ids:
        det_failures.extend(det_result.missing_fact_ids)
    if det_result.unauthorized_urls:
        det_failures.extend(det_result.unauthorized_urls)
    if det_result.unmatched_numbers_dates:
        det_failures.append(f"Unverified numbers/metrics in draft not found in facts: {', '.join(det_result.unmatched_numbers_dates[:5])}")
    if not (det_result.citation_density >= 0.5 or len(det_result.uncited_sentences) == 0):
        det_failures.append(f"Factual paragraphs missing citations: {len(det_result.uncited_sentences)} detected (density: {det_result.citation_density})")

    # Stage 2: LLM Semantic Evaluation
    facts_summary = "\n".join([
        f"[{f['id']}] {f['claim']} (Evidence: \"{f['evidence_quote']}\")"
        for f in facts
    ])

    llm = get_llm("verifier_agent")
    user_payload = (
        f"VERIFIED FACTS TABLE:\n{facts_summary}\n\n"
        f"GENERATED DRAFT TO AUDIT:\n{draft_content}"
    )

    messages = [
        SystemMessage(content=SEMANTIC_VERIFIER_SYSTEM_PROMPT),
        HumanMessage(content=user_payload),
    ]

    try:
        response = await safe_llm_invoke(llm, messages)
        raw_eval = response.content.strip()

        clean_json = raw_eval
        if "```" in clean_json:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL)
            if m:
                clean_json = m.group(1).strip()
            else:
                clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
                clean_json = re.sub(r"\n```$", "", clean_json)

        parsed = json.loads(clean_json)
        semantic_score = float(parsed.get("score", 7.0))
        detected_hallucinations = parsed.get("detected_hallucinations", [])
        unsupported_claims = parsed.get("unsupported_claims", [])
        critique = parsed.get("critique", "Audit completed.")
    except Exception as e:
        logger.warning(f"[Verifier] Semantic audit JSON parse fallback: {e}")
        semantic_score = 7.0
        detected_hallucinations = []
        unsupported_claims = []
        critique = "Audit completed with deterministic fallback."

    # Combine scores
    final_score = semantic_score
    if not det_result.passed:
        final_score = min(final_score, 6.0)
        critique = f"Deterministic checks failed: {'; '.join(det_failures)}. {critique}"

    is_passed = (
        det_result.passed and
        final_score >= 8.0
    )

    return VerificationReport(
        score=round(final_score, 1),
        passed=is_passed,
        deterministic_passed=det_result.passed,
        deterministic_failures=det_failures,
        detected_hallucinations=detected_hallucinations,
        unsupported_claims=unsupported_claims,
        critique=critique,
        status="passed" if is_passed else "revising"
    )
