import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.schema.api_schema import BlogGenerationRequest, BlogGenerationResponse, BlogPostSummary
from backend.app.schema.state_schema import BlogState
from backend.app.agent.nodes import generate_content_node


def test_blog_generation_request_word_count_defaults_and_validation():
    # Default is 800
    req = BlogGenerationRequest(topic="AI Agents in 2026")
    assert req.word_count == 800

    # Custom valid word counts
    req2 = BlogGenerationRequest(topic="AI Agents in 2026", word_count=500)
    assert req2.word_count == 500

    req3 = BlogGenerationRequest(topic="AI Agents in 2026", word_count=2500)
    assert req3.word_count == 2500

    # Below minimum (300) should raise ValidationError
    with pytest.raises(ValidationError):
        BlogGenerationRequest(topic="AI Agents in 2026", word_count=200)

    # Above maximum (4000) should raise ValidationError
    with pytest.raises(ValidationError):
        BlogGenerationRequest(topic="AI Agents in 2026", word_count=5000)


def test_blog_generation_response_contains_word_counts():
    resp = BlogGenerationResponse(
        topic="AI Agents in 2026",
        tone="Technical",
        language="English",
        target_word_count=1200,
        word_count=1185,
        title="Engineering Autonomous Agents",
        content="Comprehensive article body...",
        execution_time_seconds=12.4,
        steps_completed=["plan_queries", "content_generator"],
    )
    assert resp.target_word_count == 1200
    assert resp.word_count == 1185


def test_blog_post_summary_contains_word_counts():
    summary = BlogPostSummary(
        id=1,
        topic="AI Agents in 2026",
        tone="Technical",
        target_language="English",
        target_word_count=1500,
        word_count=1480,
        title="Engineering Autonomous Agents",
        content="Article body...",
        execution_time_seconds=10.0,
    )
    assert summary.target_word_count == 1500
    assert summary.word_count == 1480


@pytest.mark.asyncio
async def test_generate_content_node_injects_target_word_count_and_computes_actual():
    mock_llm_response = MagicMock()
    mock_llm_response.content = (
        "## Introduction\n\n"
        "Autonomous agents are evolving rapidly [F1]. Here is an in-depth breakdown of multi-agent DAGs.\n\n"
        "## Deep Dive\n\n"
        "State machine workflows allow deterministic verification loops [F2].\n"
    )

    state: BlogState = {
        "topic": "Autonomous AI Agents",
        "tone": "Technical",
        "target_language": "English",
        "target_word_count": 1200,
        "word_count": 0,
        "creativity": "balanced",
        "title": "Engineering Autonomous Agents in 2026",
        "facts": [
            {"id": "F1", "claim": "Agents evolving", "source_url": "https://tech.com/1", "domain": "tech.com"},
            {"id": "F2", "claim": "State machines verified", "source_url": "https://tech.com/2", "domain": "tech.com"},
        ],
        "research_data": "| F1 | Agents evolving | tech.com | 2026 | quote |",
        "sources": [{"url": "https://tech.com/1"}, {"url": "https://tech.com/2"}],
        "steps_completed": [],
        "revision_count": 0,
    }

    with patch("backend.app.agent.nodes.safe_llm_invoke", new_callable=AsyncMock) as mock_invoke, \
         patch("backend.app.agent.nodes.record_node_step", new_callable=AsyncMock):
        
        mock_invoke.return_value = mock_llm_response
        
        result = await generate_content_node(state)

        assert result["target_word_count"] == 1200
        assert result["word_count"] > 10
        assert "content" in result
        assert "## Sources" in result["content"]

        # Verify that prompt sent to LLM contains the target word count
        call_args = mock_invoke.call_args[0]
        messages = call_args[1]
        human_msg = messages[1].content
        assert "1200 words" in human_msg
