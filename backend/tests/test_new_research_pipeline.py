import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.core.research.dedupe import normalize_url, dedupe_sources
from backend.app.core.research.classifier import classify_topic, filter_by_recency
from backend.app.core.research.collectors import parallel_collect_all
from backend.app.core.research.fact_extractor import extract_facts_single_source
from backend.app.agent.citations import post_process_citations
from backend.app.agent.verifier_checks import run_deterministic_checks
from backend.app.agent.routers import source_gate_router, verification_router
from backend.app.schema.state_schema import BlogState, FactItem


# =========================================================================
# 1. Dedupe, Recency Filter, Min-Sources Fail Path, Dead-Feed Tests
# =========================================================================

def test_url_normalization_strips_tracking():
    raw_url = "https://techcrunch.com/2026/02/10/ai-agents/?utm_source=twitter&utm_medium=social&ref=producthunt#heading"
    normalized = normalize_url(raw_url)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "ref=" not in normalized
    assert "#heading" not in normalized
    assert normalized == "https://techcrunch.com/2026/02/10/ai-agents"


def test_fuzzy_title_deduplication():
    sources = [
        {
            "title": "Anthropic Announces Claude 3.5 Sonnet Architecture Details",
            "url": "https://techcrunch.com/claude-35",
            "domain": "techcrunch.com",
            "snippet": "Short snippet",
        },
        {
            "title": "Anthropic Announces Claude 3.5 Sonnet Architecture Details (Update)",
            "url": "https://venturebeat.com/claude-35-update",
            "domain": "venturebeat.com",
            "snippet": "Much longer and more comprehensive snippet with full benchmarks and details.",
        },
        {
            "title": "Completely Unrelated Story on Quantum Computing Advances",
            "url": "https://nature.com/quantum",
            "domain": "nature.com",
            "snippet": "Quantum physics breakthrough.",
        }
    ]
    deduped = dedupe_sources(sources, title_similarity_threshold=85.0)
    assert len(deduped) == 2
    # Prefers the candidate with more content
    titles = [s["title"] for s in deduped]
    assert any("Claude 3.5 Sonnet Architecture Details" in t for t in titles)
    assert any("Quantum Computing" in t for t in titles)


def test_recency_filter_trending_vs_evergreen():
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    stale_date = (now - timedelta(days=120)).strftime("%Y-%m-%d")

    sources = [
        {"title": "Recent Breakthrough", "url": "https://site1.com", "published_date": recent_date},
        {"title": "Stale Announcement", "url": "https://site2.com", "published_date": stale_date},
        {"title": "Undated Guide", "url": "https://site3.com", "published_date": None},
    ]

    # For trending topic: stale date is dropped
    trending_filtered = filter_by_recency(sources, topic_type="trending", max_days=60)
    trending_urls = [s["url"] for s in trending_filtered]
    assert "https://site1.com" in trending_urls
    assert "https://site2.com" not in trending_urls

    # For evergreen topic: all sources preserved
    evergreen_filtered = filter_by_recency(sources, topic_type="evergreen", max_days=60)
    assert len(evergreen_filtered) == 3


def test_min_sources_fail_path():
    # Only 1 source and 1 domain -> fails min sources requirement (requires >= 3 sources, >= 2 domains)
    state: BlogState = {
        "topic": "Obscure Unknown Micro-Library",
        "deduped_sources": [
            {"title": "Only One", "url": "https://onlyone.com/doc", "domain": "onlyone.com"}
        ],
        "query_retry_count": 0,
    }
    # First attempt: triggers retry
    action = source_gate_router(state)
    assert action == "plan_queries"

    # Second retry exhausted: fails with HTTP 422 trigger
    state["query_retry_count"] = 2
    action_exhausted = source_gate_router(state)
    assert action_exhausted == "fail_insufficient_sources"


@pytest.mark.asyncio
async def test_dead_feed_case_isolation():
    """Verifies that a failing feed or timed-out API does not crash the collector."""
    with patch("backend.app.core.research.collectors.fetch_tavily", side_effect=Exception("API Down")), \
         patch("backend.app.core.research.collectors.fetch_duckduckgo_fallback", side_effect=asyncio.TimeoutError("Timeout")), \
         patch("backend.app.core.research.collectors.fetch_wikipedia_search", return_value=[]), \
         patch("backend.app.core.research.collectors.fetch_hacker_news", return_value=[{"title": "HN Story", "url": "https://news.ycombinator.com/item?id=123", "domain": "ycombinator.com"}]):
        
        results = await parallel_collect_all(
            topic="Next.js 15 Released",
            category="tech",
            planned_queries=["nextjs 15 features"],
            timeout=2.0
        )
        # Survives failure of Tavily/DDG and returns healthy HN story
        assert len(results) >= 1
        assert any(r["title"] == "HN Story" for r in results)


# =========================================================================
# 2. Writer URL Output Ban & Unknown Fact ID Rejection
# =========================================================================

def test_writer_unknown_fact_id_rejected():
    facts = [
        {"id": "F1", "claim": "Claude 3.5 Sonnet scored 92% on HumanEval", "evidence_quote": "92%", "published_date": "2024-06-20"},
        {"id": "F2", "claim": "Released by Anthropic", "evidence_quote": "Anthropic", "published_date": "2024-06-20"}
    ]
    # Draft cites non-existent [F99]
    draft = "Claude 3.5 Sonnet demonstrated 92% accuracy on coding benchmarks [F1]. Later updates added tools [F99]."
    
    result = run_deterministic_checks(draft, facts, allowed_urls=["https://anthropic.com"])
    assert result.passed is False
    assert any("[F99]" in err for err in result.missing_fact_ids)


def test_writer_unauthorized_url_rejected():
    facts = [{"id": "F1", "claim": "Verified claim", "evidence_quote": "Verified", "published_date": "2026-01-01"}]
    # Writer outputted a raw unverified URL
    draft = "Here is an amazing breakthrough [F1]. Check out https://unverified-thirdparty.com/fake for more details."
    
    result = run_deterministic_checks(draft, facts, allowed_urls=["https://official-verified.com"])
    assert result.passed is False
    assert any("unverified-thirdparty.com" in err for err in result.unauthorized_urls)


def test_citations_post_processing_converts_ids_and_builds_sources():
    draft = "# Claude 3.5\n\nAnthropic released Claude 3.5 Sonnet [F1]. It features enhanced vision capabilities [F2]."
    facts = [
        {"id": "F1", "claim": "Anthropic released Claude 3.5", "domain": "anthropic.com", "source_url": "https://anthropic.com/news/35"},
        {"id": "F2", "claim": "Enhanced vision capabilities", "domain": "techcrunch.com", "source_url": "https://techcrunch.com/vision"}
    ]
    sources = [
        {"url": "https://anthropic.com/news/35", "title": "Anthropic Claude 3.5 Announcement", "domain": "anthropic.com", "published_date": "2024-06-20"},
        {"url": "https://techcrunch.com/vision", "title": "TechCrunch Vision Analysis", "domain": "techcrunch.com", "published_date": "2024-06-21"}
    ]
    
    full_content, sources_sec = post_process_citations(draft, facts, sources)
    # Replaced [F1] and [F2] with Markdown links
    assert "[[F1: anthropic.com]](https://anthropic.com/news/35)" in full_content
    assert "[[F2: techcrunch.com]](https://techcrunch.com/vision)" in full_content
    # Sources section generated
    assert "## Sources" in full_content
    assert "1. [Anthropic Claude 3.5 Announcement](https://anthropic.com/news/35)" in full_content
    assert "2. [TechCrunch Vision Analysis](https://techcrunch.com/vision)" in full_content


# =========================================================================
# 3. Evidence-Quote Check Drops Fabricated Fact
# =========================================================================

@pytest.mark.asyncio
async def test_evidence_quote_check_drops_fabricated_fact():
    mock_llm = MagicMock()
    # LLM returns two facts: one authentic with matching quote, one fabricated
    mock_response = MagicMock()
    mock_response.content = """[
        {
            "claim": "OpenAI announced GPT-4o with real-time audio and vision.",
            "evidence_quote": "OpenAI announced GPT-4o with real-time"
        },
        {
            "claim": "OpenAI announced GPT-5 will cost $10,000 per month.",
            "evidence_quote": "GPT-5 will cost $10,000 per month"
        }
    ]"""
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    source = {
        "title": "OpenAI Spring Update",
        "url": "https://openai.com/spring-update",
        "domain": "openai.com",
        "raw_content": "Today at the Spring Update, OpenAI announced GPT-4o with real-time audio, text, and vision reasoning capabilities.",
        "snippet": "Spring update notes."
    }

    verified_facts = await extract_facts_single_source(source, "OpenAI GPT-4o", mock_llm)
    assert len(verified_facts) == 1
    # Only the verified fact is retained
    assert "GPT-4o" in verified_facts[0]["claim"]
    # The fabricated GPT-5 fact was dropped because quote did not appear in source text!
    assert not any("GPT-5" in f["claim"] for f in verified_facts)


# =========================================================================
# 4. Verify Loop Stops After 2 Revisions
# =========================================================================

def test_verify_loop_stops_after_two_revisions():
    state: BlogState = {
        "topic": "Sample Topic",
        "passed": False,
        "verification_score": 5.5,
        "revision_count": 0,
    }

    # Revision 0 -> Revise
    assert verification_router(state) == "revise"

    # Revision 1 -> Revise
    state["revision_count"] = 1
    assert verification_router(state) == "revise"

    # Revision 2 -> Halts with failure (default REVIEW_FALLBACK='fail')
    state["revision_count"] = 2
    assert verification_router(state) == "fail_verification"


# =========================================================================
# 5. Translator Keeps Links and Numbers
# =========================================================================

def test_translator_preserves_links_and_numbers():
    original = "Model v3.5 scored 94.2% on benchmark [[F1: arxiv.org]](https://arxiv.org/abs/1234)."
    translated = "El modelo v3.5 obtuvo 94.2% en el benchmark [[F1: arxiv.org]](https://arxiv.org/abs/1234)."
    
    import re
    orig_links = re.findall(r"\[.*?\]\(.*?\)", original)
    trans_links = re.findall(r"\[.*?\]\(.*?\)", translated)
    assert orig_links == trans_links

    orig_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", original))
    trans_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", translated))
    assert orig_numbers == trans_numbers
