import re
import logging
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import List, Dict, Any
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid"
}


def normalize_url(raw_url: str) -> str:
    """
    Normalizes a URL by stripping tracking parameters, query fragments, and trailing slashes.
    """
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
            
        # Strip tracking query parameters
        filtered_queries = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
            if k.lower() not in TRACKING_PARAMS
        ]
        new_query = urlencode(filtered_queries)
        path = parsed.path.rstrip("/")
        if not path and not new_query:
            path = ""

        clean = urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path,
            "",
            new_query,
            ""  # Strip fragment
        ))
        return clean
    except Exception as e:
        logger.warning(f"Failed to normalize URL '{raw_url}': {e}")
        return raw_url.strip()


def extract_domain(url: str) -> str:
    """Extracts canonical domain (e.g. 'techcrunch.com')."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            return netloc[4:]
        return netloc
    except Exception:
        return "unknown"


def dedupe_sources(sources: List[Dict[str, Any]], title_similarity_threshold: float = 85.0) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of collected source dicts by:
    1. Canonical normalized URL matching.
    2. Fuzzy title similarity using RapidFuzz token_set_ratio (>= 85%).
    No embeddings used.
    """
    seen_urls = set()
    url_deduped: List[Dict[str, Any]] = []

    # 1. Exact canonical URL deduplication
    for s in sources:
        url = normalize_url(s.get("url", ""))
        if not url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        s["url"] = url
        s["domain"] = extract_domain(url)
        url_deduped.append(s)

    # 2. Fuzzy title similarity deduplication
    final_sources: List[Dict[str, Any]] = []
    for candidate in url_deduped:
        candidate_title = (candidate.get("title") or "").strip()
        if not candidate_title:
            continue
        
        is_duplicate = False
        for existing in final_sources:
            existing_title = (existing.get("title") or "").strip()
            score = fuzz.token_set_ratio(candidate_title, existing_title)
            if score >= title_similarity_threshold:
                # If duplicate title, prefer the one with longer snippet or text
                candidate_len = len(candidate.get("snippet", "") or "") + len(candidate.get("raw_content", "") or "")
                existing_len = len(existing.get("snippet", "") or "") + len(existing.get("raw_content", "") or "")
                if candidate_len > existing_len:
                    # Replace existing with higher content candidate
                    final_sources.remove(existing)
                    final_sources.append(candidate)
                is_duplicate = True
                break

        if not is_duplicate:
            final_sources.append(candidate)

    logger.info(f"[Dedupe] Reduced {len(sources)} raw sources down to {len(final_sources)} unique sources.")
    return final_sources
