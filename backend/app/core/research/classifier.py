import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

TRENDING_INDICATORS = {
    "2026", "2025", "latest", "recent", "new", "update", "updates", "launch",
    "releases", "release", "announces", "announced", "announcement", "trend",
    "trends", "trending", "today", "yesterday", "this week", "this month",
    "breakthrough", "q1", "q2", "q3", "q4"
}

EVERGREEN_INDICATORS = {
    "what is", "how to", "tutorial", "guide", "overview", "introduction",
    "fundamentals", "basics", "principles", "architecture", "explained",
    "deep dive", "history", "comparative study", "best practices"
}


def classify_topic(topic: str) -> Dict[str, str]:
    """
    Classifies a topic into:
    - topic_type: 'trending' or 'evergreen'
    - category: 'ai', 'tech', 'health', 'finance', or 'general'
    """
    t_lower = topic.lower().strip()

    # 1. Category Classification
    ai_keywords = ["ai", "llm", "gpt", "rag", "langgraph", "langchain", "groq", "anthropic", "machine learning", "deep learning", "agentic", "claude", "gemini", "openai"]
    tech_keywords = ["software", "api", "python", "javascript", "typescript", "cloud", "aws", "docker", "kubernetes", "database", "sql", "linux", "react", "fastapi", "github", "code"]
    health_keywords = ["health", "medical", "hospital", "doctor", "medicine", "clinical", "disease", "patient", "wellness", "pharma", "biotech"]
    finance_keywords = ["finance", "stock", "crypto", "bitcoin", "ethereum", "market", "economy", "investing", "banking", "treasury", "inflation"]

    if any(k in t_lower for k in ai_keywords):
        category = "ai"
    elif any(k in t_lower for k in tech_keywords):
        category = "tech"
    elif any(k in t_lower for k in health_keywords):
        category = "health"
    elif any(k in t_lower for k in finance_keywords):
        category = "finance"
    else:
        category = "general"

    # 2. Topic Type Classification (Trending vs Evergreen)
    has_trending_kw = any(w in t_lower for w in TRENDING_INDICATORS)
    has_evergreen_kw = any(w in t_lower for w in EVERGREEN_INDICATORS)

    if has_trending_kw:
        topic_type = "trending"
    else:
        # Default to evergreen for conceptual, lifestyle, humanities, and general topics
        # Only explicitly time-sensitive topics (with year/news keywords) are trending
        topic_type = "evergreen"

    logger.info(f"[Classifier] Topic: '{topic[:40]}...' -> Type: {topic_type}, Category: {category}")
    return {
        "topic_type": topic_type,
        "category": category,
    }


def parse_date_to_utc(date_str: Optional[str]) -> Optional[datetime]:
    """Attempts to parse diverse date formats into UTC datetime."""
    if not date_str:
        return None
    d = date_str.strip()
    
    # ISO formats
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(d[:19], fmt[:19])
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

    # RFC2822 / RSS format
    try:
        dt = parsedate_to_datetime(d)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def filter_by_recency(
    sources: List[Dict[str, Any]],
    topic_type: str,
    max_days: int = 60
) -> List[Dict[str, Any]]:
    """
    Applies recency window strictly to 'trending' topics while preserving all sources for 'evergreen'.
    Gracefully handles missing publication dates without throwing away all undated evidence.
    """
    if topic_type != "trending":
        return sources

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_days)

    dated_recent = []
    undated = []

    for s in sources:
        pub_raw = s.get("published_date")
        dt = parse_date_to_utc(pub_raw)
        if dt:
            if dt >= cutoff:
                s["published_date"] = dt.strftime("%Y-%m-%d")
                dated_recent.append(s)
            else:
                logger.debug(f"[Recency Filter] Dropped stale source ({dt.strftime('%Y-%m-%d')} < {cutoff.strftime('%Y-%m-%d')}): {s.get('title')}")
        else:
            undated.append(s)

    # If we have enough dated recent sources, use them; otherwise retain undated sources
    if len(dated_recent) >= 3:
        return dated_recent
    else:
        # Combine dated recent with undated items
        return dated_recent + undated
