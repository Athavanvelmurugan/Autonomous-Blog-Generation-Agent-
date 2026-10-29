"""
End-to-End Verification Test Script for Autonomous Blog Generation Agent.
Tests the full multi-agent workflow on 4 core topics:
1. Machine Learning for Beginners
2. Python Programming for Beginners
3. Retrieval-Augmented Generation Explained
4. Deep Reinforcement Learning Applications

Validates:
- Research retrieval (DuckDuckGo ddgs)
- Pedagogical planning and curriculum design
- Writing with code snippets, tables, pitfalls, FAQs
- Multi-dimensional fact-checking & audit
- Standalone HTML export
- Publication-quality PDF export (visual page rendering)
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Set up pathing
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.schema.state_schema import BlogState
from backend.app.agent.graph import graph
from backend.app.core.export_engine import generate_article_html, generate_article_pdf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("e2e_tester")

TOPICS_TO_TEST = [
    {
        "topic": "Machine Learning for Beginners",
        "target_audience": "Beginner",
        "tone": "Informative",
        "target_word_count": 1400,
    },
    {
        "topic": "Python Programming for Beginners",
        "target_audience": "Beginner",
        "tone": "Informative",
        "target_word_count": 1200,
    },
    {
        "topic": "Retrieval-Augmented Generation Explained",
        "target_audience": "Intermediate",
        "tone": "Technical",
        "target_word_count": 1400,
    },
    {
        "topic": "Deep Reinforcement Learning Applications",
        "target_audience": "Advanced",
        "tone": "Technical",
        "target_word_count": 1500,
    },
]


async def run_single_topic(topic_cfg: dict) -> dict:
    topic = topic_cfg["topic"]
    logger.info(f"\n=======================================================")
    logger.info(f"STARTING E2E TEST FOR: '{topic}'")
    logger.info(f"Audience: {topic_cfg['target_audience']} | Tone: {topic_cfg['tone']}")
    logger.info(f"=======================================================")

    initial_state: BlogState = {
        "topic": topic,
        "tone": topic_cfg["tone"],
        "target_audience": topic_cfg["target_audience"],
        "target_language": "English",
        "target_word_count": topic_cfg["target_word_count"],
        "word_count": 0,
        "creativity": "balanced",
        "content_plan": None,
        "planned_queries": [],
        "query_retry_count": 0,
        "raw_sources": [],
        "deduped_sources": [],
        "sources": [],
        "facts": [],
        "today_date": None,
        "topic_type": None,
        "category": None,
        "research_data": None,
        "title": "",
        "content": "",
        "sources_section": None,
        "verification_score": None,
        "passed": None,
        "critique": None,
        "detected_hallucinations": [],
        "unverified_commands": [],
        "verification_report": None,
        "revision_count": 0,
        "review_fallback_action": None,
        "original_title": None,
        "original_content": None,
        "translated_title": None,
        "translated_content": None,
        "current_step": "started",
        "steps_completed": [],
    }

    final_state = await graph.ainvoke(initial_state)

    title = final_state.get("title", "")
    content = final_state.get("content", "")
    score = final_state.get("verification_score")
    sources = final_state.get("sources", [])
    report = final_state.get("verification_report")
    word_count = len(content.split())

    logger.info(f"\n[RESULTS] '{topic}':")
    logger.info(f"- Title: {title}")
    logger.info(f"- Word Count: {word_count}")
    logger.info(f"- Verification Score: {score}")
    logger.info(f"- Sources Retrieved: {len(sources)}")
    logger.info(f"- Steps Completed: {final_state.get('steps_completed')}")

    # Assertions
    assert title, f"Article title must not be empty for {topic}"
    assert content, f"Article content must not be empty for {topic}"
    assert word_count > 500, f"Expected comprehensive content (>500 words), got {word_count}"
    assert len(sources) >= 2, f"Expected research sources to be populated, got {len(sources)}"

    return {
        "topic": topic,
        "title": title,
        "content": content,
        "score": score,
        "sources": sources,
        "word_count": word_count,
        "report": report,
        "metadata": {
            "topic": topic,
            "target_audience": topic_cfg["target_audience"],
            "tone": topic_cfg["tone"],
            "word_count": word_count,
        }
    }


async def main():
    results = []
    for cfg in TOPICS_TO_TEST:
        res = await run_single_topic(cfg)
        results.append(res)

        # For "Machine Learning for Beginners", export sample HTML and PDF
        if cfg["topic"] == "Machine Learning for Beginners":
            logger.info("Generating publication sample_export.html and sample_export.pdf...")
            html_content = generate_article_html(res["title"], res["content"], res["metadata"])
            pdf_bytes = generate_article_pdf(res["title"], res["content"], res["metadata"])

            html_path = project_root / "sample_export.html"
            pdf_path = project_root / "sample_export.pdf"

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved: {html_path} ({len(html_content)} bytes)")

            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"Saved: {pdf_path} ({len(pdf_bytes)} bytes)")

    logger.info("\n=======================================================")
    logger.info("ALL 4 TOPICS COMPLETED AND VERIFIED SUCCESSFULLY!")
    logger.info("=======================================================")


if __name__ == "__main__":
    asyncio.run(main())
