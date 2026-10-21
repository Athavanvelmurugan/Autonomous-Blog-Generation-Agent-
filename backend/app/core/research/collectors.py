import re
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
import yaml
import feedparser

from backend.app.config import get_settings
from backend.app.core.research.search_cache import search_cache
from backend.app.core.research.dedupe import extract_domain

logger = logging.getLogger(__name__)

# Load pluggable feeds configuration
FEEDS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "feeds.yaml"


def load_feeds_config() -> Dict[str, Any]:
    if not FEEDS_CONFIG_PATH.exists():
        logger.warning(f"feeds.yaml not found at {FEEDS_CONFIG_PATH}")
        return {"categories": {}}
    try:
        with open(FEEDS_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"categories": {}}
    except Exception as e:
        logger.error(f"Error loading feeds.yaml: {e}")
        return {"categories": {}}


FEEDS_CONFIG = load_feeds_config()


async def fetch_tavily(
    query: str,
    timeout: float = 10.0,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Fetches search results via Tavily Search API with cache and isolated error handling."""
    settings = get_settings()
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        logger.debug("[Tavily Collector] No TAVILY_API_KEY configured.")
        return []

    cache_key = f"tavily:{query}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    results: List[Dict[str, Any]] = []
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        # Run synchronous client search in thread pool with timeout
        loop = asyncio.get_running_loop()
        resp = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.search(query=query, search_depth="basic", max_results=max_results)
            ),
            timeout=timeout
        )
        
        for item in resp.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            content = item.get("content", "")
            pub_date = item.get("published_date")
            results.append({
                "title": title,
                "url": url,
                "domain": extract_domain(url),
                "published_date": pub_date,
                "snippet": content[:600],
                "raw_content": content,
                "source_type": "tavily",
            })
        search_cache.set(cache_key, results)
        logger.info(f"[Tavily Collector] Retrieved {len(results)} sources for '{query}'")
    except asyncio.TimeoutError:
        logger.warning(f"[Tavily Collector] Timed out after {timeout}s for query '{query}'")
    except Exception as e:
        logger.warning(f"[Tavily Collector] Search failed for query '{query}': {e}")

    return results


async def fetch_wikipedia_search(
    query: str,
    timeout: float = 6.0,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """Fetches encyclopedic context from Wikipedia REST API using full-text search with policy-compliant headers."""
    cache_key = f"wiki:{query}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    results = []
    headers = {"User-Agent": "AutonomousBlogResearcher/2.0 (research@articleproject.org)"}
    try:
        async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "format": "json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                search_items = data.get("query", {}).get("search", [])
                query_terms = [
                    w.lower() for w in query.split()
                    if len(w) > 3 and w.lower() not in {"periods", "period", "history", "timeline", "overview", "article", "guide", "about", "write", "blog"}
                ]
                matched_items = []
                for item in search_items:
                    t = item.get("title", "")
                    snippet = item.get("snippet", "").lower()
                    if not t:
                        continue
                    if not query_terms or any(term in t.lower() or term in snippet for term in query_terms):
                        matched_items.append(item)
                    if len(matched_items) >= max_results:
                        break

                for item in matched_items:
                    t = item.get("title", "")
                    try:
                        title_slug = t.replace(" ", "_")
                        s_res = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_slug}")
                        if s_res.status_code == 200:
                            s_data = s_res.json()
                            extract = s_data.get("extract", "").strip()
                            page_url = s_data.get("content_urls", {}).get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{title_slug}"
                            if extract and len(extract) > 40:
                                results.append({
                                    "title": s_data.get("title", t),
                                    "url": page_url,
                                    "domain": "en.wikipedia.org",
                                    "published_date": None,
                                    "snippet": extract[:500],
                                    "raw_content": extract,
                                    "source_type": "wikipedia",
                                })
                    except Exception:
                        pass
        if results:
            search_cache.set(cache_key, results)
            logger.info(f"[Wikipedia Collector] Retrieved {len(results)} articles for '{query}'")
    except Exception as e:
        logger.warning(f"[Wikipedia Collector] Failed for query '{query}': {e}")

    return results


async def fetch_duckduckgo_fallback(
    query: str,
    timeout: float = 8.0,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Fallback search using DuckDuckGo when Tavily is not configured."""
    cache_key = f"ddg:{query}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    results = []
    try:
        from duckduckgo_search import DDGS
        loop = asyncio.get_running_loop()

        def _search_ddg():
            try:
                # Default backend in ddgs / duckduckgo_search is the active, non-deprecated endpoint
                res = list(DDGS().text(query, max_results=max_results))
                if res:
                    return res
            except Exception:
                pass
            try:
                res = list(DDGS().text(query, max_results=max_results, backend="lite"))
                if res:
                    return res
            except Exception:
                pass
            try:
                return list(DDGS().text(query, max_results=max_results, backend="html"))
            except Exception:
                return []

        ddgs_data = await asyncio.wait_for(
            loop.run_in_executor(None, _search_ddg),
            timeout=timeout
        )
        for item in ddgs_data:
            url = item.get("href", "")
            title = item.get("title", "")
            body = item.get("body", "")
            if url and title:
                results.append({
                    "title": title,
                    "url": url,
                    "domain": extract_domain(url),
                    "published_date": None,
                    "snippet": body[:500],
                    "raw_content": body,
                    "source_type": "duckduckgo",
                })
        if results:
            search_cache.set(cache_key, results)
        logger.info(f"[DuckDuckGo Fallback] Retrieved {len(results)} sources for '{query}'")
    except Exception as e:
        logger.warning(f"[DuckDuckGo Fallback] Failed for query '{query}': {e}")

    return results


async def fetch_hacker_news(
    query: str,
    timeout: float = 8.0,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Queries HackerNews Algolia Search API for relevant tech/AI discussions."""
    cache_key = f"hn:{query}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    results = []
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "tags": "story", "hitsPerPage": max_results},
                headers={"User-Agent": "AutonomousBlogAgent/2.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("hits", []):
                    title = hit.get("title") or hit.get("story_title") or "HN Update"
                    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    created_at = hit.get("created_at", "")[:10]
                    text = hit.get("story_text") or f"HackerNews discussion with {hit.get('points', 0)} points."
                    results.append({
                        "title": title,
                        "url": url,
                        "domain": extract_domain(url),
                        "published_date": created_at or None,
                        "snippet": text[:500],
                        "raw_content": text,
                        "source_type": "hn",
                    })
                search_cache.set(cache_key, results)
                logger.info(f"[HackerNews Collector] Retrieved {len(results)} stories for '{query}'")
    except Exception as e:
        logger.warning(f"[HackerNews Collector] Failed for query '{query}': {e}")

    return results


async def fetch_arxiv(
    query: str,
    timeout: float = 8.0,
    max_results: int = 4
) -> List[Dict[str, Any]]:
    """Queries ArXiv API for scientific research preprints."""
    cache_key = f"arxiv:{query}"
    cached = search_cache.get(cache_key)
    if cached is not None:
        return cached

    results = []
    try:
        clean_q = "+".join(query.split()[:4])
        url = f"http://export.arxiv.org/api/query?search_query=all:{clean_q}&start=0&max_results={max_results}"
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers={"User-Agent": "AutonomousBlogAgent/2.0"})
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    title = getattr(entry, "title", "").replace("\n", " ").strip()
                    link = getattr(entry, "link", "")
                    summary = getattr(entry, "summary", "").replace("\n", " ").strip()
                    published = getattr(entry, "published", "")[:10]
                    results.append({
                        "title": title,
                        "url": link,
                        "domain": "arxiv.org",
                        "published_date": published or None,
                        "snippet": summary[:600],
                        "raw_content": summary,
                        "source_type": "arxiv",
                    })
                search_cache.set(cache_key, results)
                logger.info(f"[ArXiv Collector] Retrieved {len(results)} papers for '{query}'")
    except Exception as e:
        logger.warning(f"[ArXiv Collector] Failed for query '{query}': {e}")

    return results


async def fetch_rss_feed(
    feed_name: str,
    feed_url: str,
    topic_keywords: List[str],
    timeout: float = 6.0
) -> List[Dict[str, Any]]:
    """Fetches and filters an RSS feed for relevant entries."""
    results = []
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "AutonomousBlogAgent/2.0"})
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:10]:
                    title = getattr(entry, "title", "").strip()
                    link = getattr(entry, "link", "").strip()
                    summary = getattr(entry, "summary", "").strip()
                    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
                    
                    # Filter for topical relevance (exclude common conversational, generic, and temporal words)
                    COMMON_STOPWORDS = {
                        "write", "blog", "about", "post", "article", "guide", "please", "with",
                        "from", "that", "this", "what", "when", "where", "have", "been", "were",
                        "will", "your", "more", "most", "some", "into", "over", "these", "those",
                        "which", "their", "there", "them", "then", "than", "each", "other", "also",
                        "history", "period", "periods", "story", "stories", "times", "world", "today",
                        "news", "report", "first", "last", "year", "years", "time", "people", "state",
                        "recent", "latest", "update", "updates", "overview", "review"
                    }
                    meaningful_keywords = [
                        k.lower() for k in topic_keywords 
                        if len(k) > 3 and k.lower() not in COMMON_STOPWORDS
                    ]
                    text_blob = f"{title} {summary}".lower()
                    matched_keys = [k for k in meaningful_keywords if k in text_blob]
                    min_matches = 2 if len(meaningful_keywords) >= 2 else 1
                    if meaningful_keywords and len(matched_keys) >= min_matches:
                        results.append({
                            "title": title,
                            "url": link,
                            "domain": extract_domain(link),
                            "published_date": published or None,
                            "snippet": summary[:500],
                            "raw_content": summary,
                            "source_type": f"rss:{feed_name}",
                        })
                logger.info(f"[RSS Collector: {feed_name}] Matched {len(results)} relevant entries.")
    except Exception as e:
        logger.warning(f"[RSS Collector: {feed_name}] Failed to fetch feed: {e}")

    return results


async def parallel_collect_all(
    topic: str,
    category: str,
    planned_queries: List[str],
    timeout: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Executes parallel multi-source ingestion across:
    1. Search API (Tavily with DDG fallback)
    2. Category-specific RSS feeds from feeds.yaml
    3. HackerNews and ArXiv (enabled strictly for tech/ai categories)
    
    Each collector has isolated error handling and independent timeouts.
    """
    settings = get_settings()
    cat_cfg = FEEDS_CONFIG.get("categories", {}).get(category, {})
    use_hn = cat_cfg.get("use_hacker_news", False)
    use_arxiv = cat_cfg.get("use_arxiv", False)
    rss_list = cat_cfg.get("rss_feeds", [])

    tasks = []
    
    # 1. Search API tasks for planned queries
    for q in planned_queries[:3]:
        if settings.TAVILY_API_KEY:
            tasks.append(fetch_tavily(q, timeout=timeout))
        else:
            tasks.append(fetch_duckduckgo_fallback(q, timeout=timeout))

    # Wikipedia encyclopedic grounding for foundational context
    clean_topic = re.sub(
        r"^(?:write\s+(?:a\s+)?(?:blog|article|post|guide)(?:\s+(?:about|on|for))?\s*|\b(?:please\s+)?generate\s+(?:a\s+)?blog\s+(?:about|on|for)?\s*)",
        "",
        topic,
        flags=re.IGNORECASE,
    ).strip() or topic
    tasks.append(fetch_wikipedia_search(clean_topic, timeout=timeout))
    if planned_queries:
        tasks.append(fetch_wikipedia_search(planned_queries[0], timeout=timeout))

    # 2. HackerNews (tech/ai only)
    if use_hn:
        for q in planned_queries[:2]:
            tasks.append(fetch_hacker_news(q, timeout=timeout))

    # 3. ArXiv (tech/ai only)
    if use_arxiv:
        tasks.append(fetch_arxiv(topic, timeout=timeout))

    # 4. RSS feeds
    topic_tokens = topic.split()
    for feed in rss_list:
        tasks.append(
            fetch_rss_feed(
                feed_name=feed.get("name", "RSS"),
                feed_url=feed.get("url", ""),
                topic_keywords=topic_tokens,
                timeout=feed.get("timeout", 6.0)
            )
        )

    # Execute all concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_sources: List[Dict[str, Any]] = []
    for resp in responses:
        if isinstance(resp, list):
            all_sources.extend(resp)
        elif isinstance(resp, Exception):
            logger.warning(f"[Parallel Collector] Sub-task encountered error: {resp}")

    logger.info(f"[Parallel Collector] Ingested {len(all_sources)} total raw candidate sources across all collectors.")
    return all_sources
