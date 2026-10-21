import re
import logging
from typing import List, Dict, Any, Tuple
from backend.app.schema.state_schema import FactItem

logger = logging.getLogger(__name__)


def post_process_citations(
    draft_content: str,
    facts: List[Dict[str, Any]],
    sources: List[Dict[str, Any]]
) -> Tuple[str, str]:
    """
    Post-processes the blog draft by:
    1. Converting internal fact citations (e.g. [F1], [F2]) into clickable Markdown hyperlinks.
       Format: `[[F1: domain]](url)` or `[[F1]](url)`
    2. Generating a clean, deduplicated '## Sources' appendix at the bottom of the article.
    3. Ensuring the writer never had to write raw URLs.
    """
    facts_by_id = {f["id"].upper(): f for f in facts}
    used_fact_ids = set()

    def replace_citation(match):
        raw_id = match.group(1).upper()
        if raw_id in facts_by_id:
            used_fact_ids.add(raw_id)
            fact = facts_by_id[raw_id]
            url = fact.get("source_url") or "#"
            domain = fact.get("domain") or "source"
            return f"[[{raw_id}: {domain}]]({url})"
        # If unknown fact ID, keep as is
        return match.group(0)

    # 1. Replace [F1], [F2], etc.
    processed_content = re.sub(r"\[(F\d+)\]", replace_citation, draft_content)

    # 2. Build Sources appendix
    # Collect unique source URLs cited in the draft
    cited_urls = set()
    for fid in used_fact_ids:
        url = facts_by_id[fid].get("source_url")
        if url:
            cited_urls.add(url)

    # Match cited URLs against collected sources list
    sources_by_url = {s.get("url"): s for s in sources if s.get("url")}
    
    source_lines = ["\n\n## Sources\n"]
    idx = 1
    
    # Priority: List cited sources first
    for url in sorted(cited_urls):
        s_info = sources_by_url.get(url, {})
        title = s_info.get("title") or facts_by_id.get(list(used_fact_ids)[0], {}).get("domain") or "Reference Source"
        domain = s_info.get("domain") or "external"
        date_str = f" ({s_info.get('published_date')})" if s_info.get("published_date") else ""
        source_lines.append(f"{idx}. [{title}]({url}) - *{domain}*{date_str}")
        idx += 1

    # If no specific citations matched or empty, list top verified sources
    if len(cited_urls) == 0 and sources:
        for s in sources[:5]:
            url = s.get("url", "#")
            title = s.get("title", "Reference Source")
            domain = s.get("domain", "external")
            date_str = f" ({s.get('published_date')})" if s.get("published_date") else ""
            source_lines.append(f"{idx}. [{title}]({url}) - *{domain}*{date_str}")
            idx += 1

    sources_section = "\n".join(source_lines)
    full_content = processed_content + sources_section
    return full_content, sources_section
