import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.config import get_settings
from backend.app.schema.state_schema import BlogState, FactItem, VerificationReport
from backend.app.core.prompts import (
    QUERY_PLANNING_SYSTEM_PROMPT,
    TITLE_SYSTEM_PROMPT,
    CONTENT_SYSTEM_PROMPT,
    VERIFIER_SYSTEM_PROMPT,
    TRANSLATION_SYSTEM_PROMPT,
)
from backend.app.core.llm import get_llm, get_node_config
from backend.app.core.groq_guard import safe_llm_invoke
from backend.app.agent.persistence import record_node_step
from backend.app.core.research.classifier import classify_topic, filter_by_recency
from backend.app.core.research.collectors import parallel_collect_all
from backend.app.core.research.dedupe import dedupe_sources
from backend.app.core.research.fact_extractor import parallel_extract_facts
from backend.app.agent.citations import post_process_citations
from backend.app.agent.verifier_checks import run_full_verification

logger = logging.getLogger(__name__)
settings = get_settings()


# ==========================================
# 1. Query Planning Node
# ==========================================
async def plan_queries_node(state: BlogState) -> dict:
    """
    Node 1: Analyzes the topic, injects today's date, classifies topic type,
    and plans 3-4 diverse, high-precision search queries.
    """
    start_time = time.perf_counter()
    topic = state["topic"].strip()
    retry_count = state.get("query_retry_count", 0)
    
    # Inject today's date if not present
    today_date = state.get("today_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Classify topic
    classification = classify_topic(topic)
    topic_type = state.get("topic_type") or classification["topic_type"]
    category = state.get("category") or classification["category"]

    logger.info(
        f"[Node 1: Plan Queries] Topic: '{topic[:40]}...' (Type: {topic_type}, "
        f"Category: {category}, Date: {today_date}, Retry #{retry_count})"
    )

    llm = get_llm("plan_queries")
    user_payload = (
        f"Topic: {topic}\n"
        f"Current Date: {today_date}\n"
        f"Topic Type: {topic_type}\n"
        f"Category: {category}\n"
    )
    if retry_count > 0:
        user_payload += (
            f"NOTE: Previous queries yielded insufficient sources. "
            f"Generate BROADER queries targeting official releases, news, and foundational overview."
        )

    messages = [
        SystemMessage(content=QUERY_PLANNING_SYSTEM_PROMPT),
        HumanMessage(content=user_payload),
    ]

    queries: List[str] = []
    try:
        response = await safe_llm_invoke(llm, messages)
        raw_output = response.content.strip()

        clean_json = raw_output
        if "```" in clean_json:
            m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", clean_json, re.DOTALL)
            if m:
                clean_json = m.group(1).strip()
            else:
                clean_json = re.sub(r"^```[a-zA-Z]*\n", "", clean_json)
                clean_json = re.sub(r"\n```$", "", clean_json)

        parsed = json.loads(clean_json)
        if isinstance(parsed, list):
            queries = [str(q).strip() for q in parsed if str(q).strip()]
    except Exception as e:
        logger.warning(f"[Plan Queries] JSON parsing failed: {e}. Generating fallback query set.")

    if not queries:
        # Strip conversational prompt phrases (e.g., 'write a blog about ...')
        clean_topic = re.sub(
            r"^(?:write\s+(?:a\s+)?(?:blog|article|post|guide)(?:\s+(?:about|on|for))?\s*|\b(?:please\s+)?generate\s+(?:a\s+)?blog\s+(?:about|on|for)?\s*)",
            "",
            topic,
            flags=re.IGNORECASE,
        ).strip()
        if not clean_topic:
            clean_topic = topic

        year = today_date[:4]
        if topic_type == "evergreen":
            queries = [
                f"{clean_topic} history overview",
                f"{clean_topic} timeline origins architecture",
                f"{clean_topic} records documentation",
            ]
        else:
            queries = [
                f"{clean_topic} overview analysis",
                f"{clean_topic} {year} news updates",
                f"{clean_topic} official documentation",
            ]

    steps = list(state.get("steps_completed", []))
    if "plan_queries" not in steps:
        steps.append("plan_queries")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["plan_queries"] = round(time.perf_counter() - start_time, 3)

    prior_steps = state.get("steps_completed", [])
    effective_retry = retry_count + 1 if "clean_dedupe" in prior_steps else retry_count

    result = {
        "planned_queries": queries,
        "query_retry_count": effective_retry,
        "today_date": today_date,
        "topic_type": topic_type,
        "category": category,
        "current_step": "plan_queries_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    llm_metrics = {"provider": settings.MODEL_PROVIDER, "model": settings.MODEL_NAME, "temperature": 0.0}
    await record_node_step("plan_queries", state, result, start_time, llm_metrics)
    return result


# ==========================================
# 2. Multi-Source Collection Node
# ==========================================
async def collect_node(state: BlogState) -> dict:
    """
    Node 2: Concurrently fetches candidate articles from Search API (Tavily/DDG),
    category-specific RSS feeds, and Hacker News / ArXiv with error isolation and timeouts.
    """
    start_time = time.perf_counter()
    topic = state["topic"]
    category = state.get("category", "general")
    planned_queries = state.get("planned_queries", [topic])
    timeout = getattr(settings, "SEARCH_TIMEOUT_SECONDS", 10.0)

    logger.info(f"[Node 2: Collect] Launching parallel fetch across multi-sources for {len(planned_queries)} queries...")
    raw_collected = await parallel_collect_all(
        topic=topic,
        category=category,
        planned_queries=planned_queries,
        timeout=timeout
    )

    # Accumulate with any prior raw sources from retries
    existing_raw = list(state.get("raw_sources", []))
    combined_raw = existing_raw + raw_collected

    steps = list(state.get("steps_completed", []))
    if "collect" not in steps:
        steps.append("collect")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["collect"] = round(time.perf_counter() - start_time, 3)

    result = {
        "raw_sources": combined_raw,
        "current_step": "collect_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    await record_node_step("collect", state, result, start_time, None)
    return result


# ==========================================
# 3. Clean & Deduplicate Node
# ==========================================
async def clean_dedupe_node(state: BlogState) -> dict:
    """
    Node 3: Normalizes URLs, deduplicates titles using RapidFuzz, applies recency filtering
    strictly to trending topics, and evaluates the minimum-sources requirement.
    """
    start_time = time.perf_counter()
    raw_sources = state.get("raw_sources", [])
    topic_type = state.get("topic_type", "trending")
    min_sources = getattr(settings, "MIN_SOURCES_REQUIRED", 3)

    logger.info(f"[Node 3: Clean & Dedupe] Processing {len(raw_sources)} raw sources (Type: {topic_type})...")
    
    # 1. URL Normalization + Fuzzy Title Deduplication (no embeddings)
    deduped = dedupe_sources(raw_sources)

    # 2. Recency Filtering (applied only to trending topics)
    filtered = filter_by_recency(deduped, topic_type=topic_type)

    # Prioritize authoritative sources with substantive content length (e.g. Wikipedia)
    filtered.sort(
        key=lambda s: (
            1 if "wikipedia.org" in (s.get("domain") or "") else 0,
            len(s.get("raw_content") or s.get("snippet") or "")
        ),
        reverse=True
    )

    distinct_domains = {s.get("domain") for s in filtered if s.get("domain")}
    is_sufficient = len(filtered) >= min_sources and len(distinct_domains) >= 2

    # Verify topical grounding for specific entity names/keywords
    topic_clean = re.sub(
        r"^(?:write\s+(?:a\s+)?(?:blog|article|post|guide)(?:\s+(?:about|on|for))?\s*|\b(?:please\s+)?generate\s+(?:a\s+)?blog\s+(?:about|on|for)?\s*)",
        "",
        state.get("topic", ""),
        flags=re.IGNORECASE,
    ).strip()
    distinctive_terms = [
        w.lower().rstrip("s") for w in re.findall(r"\b[a-zA-Z0-9_-]{6,}\b", topic_clean)
        if w.lower() not in {"history", "architecture", "overview", "review", "protocol", "quantum", "concurrency", "performance", "processing", "threading", "models", "period", "periods", "system", "systems", "release", "releases", "internal", "framework"}
    ]
    error_msg = None
    if is_sufficient and distinctive_terms:
        all_text = " ".join([f"{s.get('title', '')} {s.get('url', '')} {s.get('snippet', '')}" for s in filtered]).lower()
        if not any(term in all_text for term in distinctive_terms):
            is_sufficient = False
            error_msg = f"Insufficient ground-truth sources: No collected sources match distinctive entity '{distinctive_terms[0]}'. Halting to prevent ungrounded writing."

    if not is_sufficient and not error_msg:
        error_msg = (
            f"Insufficient ground-truth sources found: retrieved {len(filtered)} valid sources across "
            f"{len(distinct_domains)} distinct domains. Required at least {min_sources} sources across 2 distinct domains."
        )
    if error_msg:
        logger.warning(f"[Clean & Dedupe] {error_msg}")

    # Build backward-compatible research context snippet string
    context_snippets = []
    for s in filtered[:5]:
        context_snippets.append(f"Source: {s.get('title')} ({s.get('url')})\nFacts: {s.get('snippet')}")
    research_summary = "\n\n".join(context_snippets)

    steps = list(state.get("steps_completed", []))
    if "clean_dedupe" not in steps:
        steps.append("clean_dedupe")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["clean_dedupe"] = round(time.perf_counter() - start_time, 3)

    result = {
        "deduped_sources": filtered,
        "sources": filtered,
        "research_data": research_summary,
        "error": error_msg if not is_sufficient else None,
        "current_step": "clean_dedupe_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    await record_node_step("clean_dedupe", state, result, start_time, None)
    return result


# ==========================================
# 4. Atomic Fact Extraction Node
# ==========================================
async def extract_facts_node(state: BlogState) -> dict:
    """
    Node 4: Extracts atomic facts per source in parallel.
    Programmatically verifies that each evidence_quote is a verbatim substring of the source text.
    Assigns sequential IDs [F1, F2, ...] to verified facts.
    """
    start_time = time.perf_counter()
    deduped_sources = state.get("deduped_sources", [])
    topic = state["topic"]

    logger.info(f"[Node 4: Extract Facts] Extracting facts from {len(deduped_sources)} verified sources...")
    verified_fact_items = await parallel_extract_facts(deduped_sources, topic)

    facts_dict_list = [f.model_dump() for f in verified_fact_items]

    # Format Markdown facts table for LLM writer context
    facts_table_lines = [
        "| ID | Verified Claim | Domain | Date | Verbatim Evidence |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for f in verified_fact_items:
        date_str = f.published_date or "N/A"
        evidence_clean = f.evidence_quote.replace("|", "/")
        claim_clean = f.claim.replace("|", "/")
        facts_table_lines.append(f"| {f.id} | {claim_clean} | {f.domain} | {date_str} | \"{evidence_clean}\" |")

    facts_table_md = "\n".join(facts_table_lines)

    steps = list(state.get("steps_completed", []))
    if "extract_facts" not in steps:
        steps.append("extract_facts")

    error_msg = None
    min_facts = getattr(settings, "MIN_FACTS_REQUIRED", 3)
    if len(verified_fact_items) < min_facts:
        error_msg = (
            f"Insufficient verified atomic facts extracted: found {len(verified_fact_items)} facts. "
            f"Required at least {min_facts} verified facts to write an authoritative, non-redundant blog post."
        )
        logger.warning(f"[Node 4: Extract Facts] {error_msg}")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["extract_facts"] = round(time.perf_counter() - start_time, 3)

    result = {
        "facts": facts_dict_list,
        "research_data": facts_table_md,
        "error": error_msg,
        "current_step": "extract_facts_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    llm_metrics = {"provider": settings.MODEL_PROVIDER, "model": settings.MODEL_NAME, "temperature": 0.0}
    await record_node_step("extract_facts", state, result, start_time, llm_metrics)
    return result


# ==========================================
# 5. Title Generator Node
# ==========================================
async def generate_title_node(state: BlogState) -> dict:
    """
    Node 5: Generates an engaging, SEO-optimized title strictly grounded in verified facts.
    """
    start_time = time.perf_counter()
    creativity = state.get("creativity", "balanced")
    logger.info(f"[Node 5: Title Generator] Topic: '{state['topic']}'")
    llm = get_llm("title_generator", creativity_level=creativity)

    facts = state.get("facts", [])
    facts_preview = "\n".join([f"[{f.get('id')}] {f.get('claim')}" for f in facts[:8]]) or "No facts."

    messages = [
        SystemMessage(content=TITLE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Topic: {state['topic']}\n"
                f"Tone: {state.get('tone', 'Informative')}\n"
                f"Verified Facts Context:\n{facts_preview}"
            )
        ),
    ]

    clean_title = state["topic"]
    try:
        response = await safe_llm_invoke(llm, messages)
        raw_title = response.content.strip().strip('"\'')
        if "\n" in raw_title:
            raw_title = raw_title.split("\n")[0].strip('"\'')
        if len(raw_title) > 5:
            clean_title = raw_title
    except Exception as e:
        logger.warning(f"[Title Generator] LLM call failed: {e}")

    steps = list(state.get("steps_completed", []))
    if "title_generator" not in steps:
        steps.append("title_generator")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["title_generator"] = round(time.perf_counter() - start_time, 3)

    result = {
        "title": clean_title,
        "original_title": clean_title,
        "current_step": "title_generated",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    llm_metrics = {"provider": settings.MODEL_PROVIDER, "model": settings.MODEL_NAME, "temperature": 0.5}
    await record_node_step("title_generator", state, result, start_time, llm_metrics)
    return result


# ==========================================
# 6. Content Generator / Writer Node
# ==========================================
async def generate_content_node(state: BlogState) -> dict:
    """
    Node 6: Writes an authoritative blog post grounded strictly in the verified facts table.
    Cites fact IDs [F1], [F2] exclusively; never outputs raw URLs.
    Post-processes the draft into Markdown links and automatically creates the Sources appendix.
    """
    start_time = time.perf_counter()
    revisions = state.get("revision_count", 0)
    writer_cfg = get_node_config("content_generator")
    base_temp = writer_cfg.temperature  # 0.35 from config

    # Step down temperature by 0.1 per revision (min 0.1)
    effective_temp = max(0.1, round(base_temp - (0.1 * min(revisions, 2)), 2))
    logger.info(f"[Node 6: Writer] Drafting '{state['title']}' (Revision #{revisions}, Temp: {effective_temp})")

    llm = get_llm("content_generator", temperature_override=effective_temp)

    facts = state.get("facts", [])
    facts_table_md = state.get("research_data") or "No verified facts table available."
    today_date = state.get("today_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    prompt_content = (
        f"Title: {state['title']}\n"
        f"Topic: {state['topic']}\n"
        f"Tone: {state.get('tone', 'Informative')}\n"
        f"Current Date: {today_date}\n\n"
        f"VERIFIED FACTS TABLE (Only write claims from this table; cite every claim as [F1], [F2], etc.):\n"
        f"{facts_table_md}\n\n"
    )

    critique_context = state.get("critique")
    hallucinations = state.get("detected_hallucinations") or []
    report = state.get("verification_report") or {}
    unsupported = report.get("unsupported_claims", [])

    if revisions > 0 and (critique_context or hallucinations or unsupported):
        prompt_content += "--- CRITICAL EDITORIAL REVISION REQUIRED ---\n"
        if critique_context:
            prompt_content += f"Editorial Audit Feedback:\n{critique_context}\n\n"
        if hallucinations:
            prompt_content += "Flagged Unsupported Claims to Remove:\n"
            for h in hallucinations:
                prompt_content += f"- {h}\n"
            prompt_content += "\n"
        if unsupported:
            prompt_content += "Statements Lacking Grounding to Remove or Cite:\n"
            for u in unsupported:
                prompt_content += f"- {u}\n"
            prompt_content += "\n"
        prompt_content += "Strictly eliminate all flagged claims and cite remaining statements accurately.\n\n"

    prompt_content += (
        "Write the complete Markdown blog post now. Remember: Every factual body paragraph MUST cite "
        "at least one verified fact ID like [F1], [F2]. Do NOT write uncited filler or background claims. "
        "Do NOT write raw URLs. Do NOT write a manual Sources section."
    )

    messages = [
        SystemMessage(content=CONTENT_SYSTEM_PROMPT),
        HumanMessage(content=prompt_content),
    ]

    response = await safe_llm_invoke(llm, messages)
    raw_draft = response.content.strip()

    # Post-process citations: convert [F1] to Markdown links and append ## Sources appendix
    sources = state.get("sources", [])
    full_content, sources_section = post_process_citations(raw_draft, facts, sources)

    steps = list(state.get("steps_completed", []))
    if "content_generator" not in steps:
        steps.append("content_generator")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["content_generator"] = round(time.perf_counter() - start_time, 3)

    result = {
        "content": full_content,
        "original_content": full_content,
        "sources_section": sources_section,
        "current_step": "content_generated",
        "steps_completed": steps,
        "revision_count": revisions + 1,
        "node_timings": node_timings,
    }
    llm_metrics = {"provider": settings.MODEL_PROVIDER, "model": settings.MODEL_NAME, "temperature": effective_temp}
    await record_node_step("content_generator", state, result, start_time, llm_metrics)
    return result

# Alias for graph convention
write_node = generate_content_node


# ==========================================
# 7. Verification Node
# ==========================================
async def verify_content_node(state: BlogState) -> dict:
    """
    Node 7: Performs two-stage verification:
    Stage 1: Deterministic rule-based checks (fact IDs, numbers/dates, URLs, citation density).
    Stage 2: LLM semantic evaluation at temp 0.0 with optional VERIFIER_MODEL.
    """
    start_time = time.perf_counter()
    logger.info(f"[Node 7: Verifier Agent] Auditing content for '{state['title']}'...")

    content = state.get("content", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])

    report: VerificationReport = await run_full_verification(content, facts, sources)

    steps = list(state.get("steps_completed", []))
    if "verifier_agent" not in steps:
        steps.append("verifier_agent")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["verifier_agent"] = round(time.perf_counter() - start_time, 3)

    result = {
        "verification_score": report.score,
        "passed": report.passed,
        "critique": report.critique,
        "detected_hallucinations": report.detected_hallucinations,
        "unverified_commands": report.unverified_commands,
        "verification_report": report.model_dump(),
        "current_step": "verification_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    llm_metrics = {
        "provider": settings.MODEL_PROVIDER,
        "model": getattr(settings, "VERIFIER_MODEL", None) or settings.MODEL_NAME,
        "temperature": 0.0,
    }
    await record_node_step("verifier_agent", state, result, start_time, llm_metrics)
    return result


# ==========================================
# 8. Translation Node
# ==========================================
async def translate_content_node(state: BlogState) -> dict:
    """
    Node 8: Localizes the title and prose into target_language.
    Requirement 11: Keeps fact links, URLs, and numbers unchanged,
    and programmatically verifies link counts and numbers before and after.
    """
    start_time = time.perf_counter()
    target_lang = state.get("target_language", "English")
    logger.info(f"[Node 8: Translator] Translating into '{target_lang}' (Preserving citations & numbers)...")
    llm = get_llm("translator")

    messages = [
        SystemMessage(content=TRANSLATION_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Target Language: {target_lang}\n"
                f"Title: {state['title']}\n"
                f"Content to Localize:\n{state['content']}"
            )
        ),
    ]

    response = await safe_llm_invoke(llm, messages)
    raw_output = response.content.strip()

    translated_title = state["title"]
    translated_content = state["content"]

    if "TITLE:" in raw_output and "---" in raw_output:
        parts = raw_output.split("---", 1)
        title_part = parts[0].replace("TITLE:", "").strip()
        if title_part:
            translated_title = title_part
        if len(parts) > 1 and parts[1].strip():
            translated_content = parts[1].strip()
    else:
        translated_content = raw_output

    # Programmatic Citation & Number Invariant Check (Requirement 11)
    orig_links = re.findall(r"\[.*?\]\(.*?\)", state["content"])
    trans_links = re.findall(r"\[.*?\]\(.*?\)", translated_content)
    if len(orig_links) != len(trans_links):
        logger.warning(
            f"[Translator Invariant Warning] Link count mismatch: original had {len(orig_links)} links, "
            f"translated has {len(trans_links)} links."
        )

    orig_numbers = set(re.findall(r"\b\d+\b", state["content"]))
    trans_numbers = set(re.findall(r"\b\d+\b", translated_content))
    missing_numbers = orig_numbers - trans_numbers
    if missing_numbers:
        logger.warning(f"[Translator Invariant Warning] Numbers altered in translation: {missing_numbers}")

    steps = list(state.get("steps_completed", []))
    if "translator" not in steps:
        steps.append("translator")

    node_timings = dict(state.get("node_timings") or {})
    node_timings["translator"] = round(time.perf_counter() - start_time, 3)

    result = {
        "title": translated_title,
        "content": translated_content,
        "translated_title": translated_title,
        "translated_content": translated_content,
        "current_step": "translation_completed",
        "steps_completed": steps,
        "node_timings": node_timings,
    }
    llm_metrics = {"provider": settings.MODEL_PROVIDER, "model": settings.MODEL_NAME, "temperature": 0.2}
    await record_node_step("translator", state, result, start_time, llm_metrics)
    return result


# ==========================================
# 9. Backward Compatibility Stub
# ==========================================
async def research_trending_data_node(state: BlogState) -> dict:
    """Legacy backward-compatible adapter routing to the new factual pipeline."""
    plan_res = await plan_queries_node(state)
    state.update(plan_res)
    collect_res = await collect_node(state)
    state.update(collect_res)
    clean_res = await clean_dedupe_node(state)
    return clean_res
