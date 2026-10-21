import pytest
import uuid
from backend.app.db.database import get_async_session
from backend.app.db.repositories import (
    BlogRepository,
    RunRepository,
    TelemetryRepository,
    UserRepository,
)

@pytest.mark.asyncio
async def test_blog_repository_crud_and_pagination():
    async with get_async_session() as session:
        repo = BlogRepository(session)
        unique_topic = f"Test Keyset Topic {uuid.uuid4().hex[:8]}"

        # 1. Create Blog with Version 1
        blog = await repo.create_blog_with_version(
            topic=unique_topic,
            tone="Technical",
            target_language="English",
            title="Initial Title",
            content="# Initial Content",
            sources=[{"title": "Test Source", "url": "https://example.com/test", "snippet": "Sample snippet"}],
        )
        assert blog.id is not None
        assert blog.topic == unique_topic

        # 2. Get Blog by ID (with selectinload on versions and sources)
        fetched = await repo.get_blog_by_id(blog.id)
        assert fetched is not None
        assert fetched.id == blog.id
        assert len(fetched.versions) == 1
        assert fetched.latest_version.title == "Initial Title"

        # 3. Update Blog
        updated = await repo.update_blog(blog.id, title="Updated Title", content="# Updated Content")
        assert updated is not None
        assert updated.latest_version.title == "Updated Title"

        # 4. Keyset pagination test
        blogs, next_cursor = await repo.list_blogs(limit=5)
        assert len(blogs) > 0
        assert blogs[0].created_at is not None

        # 5. Soft delete
        deleted = await repo.delete_blog(blog.id, hard_delete=False)
        assert deleted is True

        # Confirm excluded from active list
        re_fetched = await repo.get_blog_by_id(blog.id, include_deleted=False)
        assert re_fetched is None

        # Clean up hard delete for test isolation
        await repo.delete_blog(blog.id, hard_delete=True)


@pytest.mark.asyncio
async def test_run_repository_idempotency():
    async with get_async_session() as session:
        repo = RunRepository(session)
        idemp_key = f"test_idemp_{uuid.uuid4().hex}"
        thread_id = f"thread_{idemp_key}"

        # 1. First call creates the run
        run1, is_new1 = await repo.get_or_create_run(idempotency_key=idemp_key, thread_id=thread_id)
        assert is_new1 is True
        assert run1.idempotency_key == idemp_key
        assert run1.status == "running"

        # 2. Duplicate call returns existing run without duplicate rows
        run2, is_new2 = await repo.get_or_create_run(idempotency_key=idemp_key, thread_id=thread_id)
        assert is_new2 is False
        assert run2.id == run1.id

        # 3. Record step
        step = await repo.record_run_step(
            run_id=run1.id,
            node_name="title_generator",
            step_order=1,
            input_state={"topic": "Agentic AI"},
            output_state={"title": "Mastering Agentic AI"},
            duration_seconds=0.45,
        )
        assert step.id is not None
        assert step.node_name == "title_generator"

        # 4. Update status
        updated_run = await repo.update_run_status(run1.id, status="completed", total_execution_time_seconds=1.25)
        assert updated_run.status == "completed"
        assert updated_run.total_execution_time_seconds == 1.25


@pytest.mark.asyncio
async def test_telemetry_repository_logging():
    async with get_async_session() as session:
        telemetry = TelemetryRepository(session)

        # 1. Record LLM call
        llm = await telemetry.record_llm_call(
            node_name="content_generator",
            provider="groq",
            model="openai/gpt-oss-120b",
            temperature=0.7,
            prompt_tokens=350,
            completion_tokens=650,
            cost_usd=0.002,
            latency_seconds=1.85,
        )
        assert llm.id is not None
        assert llm.total_tokens == 1000

        # 2. Batch record sources
        sources = await telemetry.batch_record_sources(
            sources=[
                {"title": "Doc 1", "url": "https://python.org", "snippet": "Python language", "domain": "python.org"},
                {"title": "Doc 2", "url": "https://fastapi.tiangolo.com", "snippet": "FastAPI framework", "domain": "tiangolo.com"},
            ]
        )
        assert len(sources) == 2
        assert sources[0].id is not None

        # 3. Record fact-check and claims
        fc = await telemetry.record_fact_check(
            score=9.2,
            passed=True,
            critique="Audited and accurate.",
            claims=[
                {"claim_text": "PostgreSQL 16 supports SIMD acceleration", "status": "verified", "evidence": "Release notes"},
            ],
        )
        assert fc.id is not None
        assert fc.score == 9.2


@pytest.mark.asyncio
async def test_user_repository_and_api_key():
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        test_email = f"user_{uuid.uuid4().hex[:6]}@example.com"

        # 1. Create user
        user = await user_repo.get_or_create_user(email=test_email, role="editor")
        assert user.id is not None
        assert user.email == test_email

        # 2. Generate API key
        api_key, raw_token = await user_repo.create_api_key(user_id=user.id, name="CI Test Key")
        assert api_key.id is not None
        assert raw_token.startswith("agy_")

        # 3. Validate raw token
        authenticated_user = await user_repo.validate_api_key(raw_token)
        assert authenticated_user is not None
        assert authenticated_user.id == user.id

        # 4. Invalid key fails
        invalid_check = await user_repo.validate_api_key("agy_non_existent_token")
        assert invalid_check is None


@pytest.mark.asyncio
async def test_blog_post_summary_with_float_reliability_score():
    """Verify that BlogPostSummary accepts float reliability_score in sources without Pydantic validation error."""
    from backend.app.schema.api_schema import BlogPostSummary
    summary = BlogPostSummary(
        id=1,
        topic="Testing Sources",
        tone="Technical",
        target_language="English",
        title="Test Title",
        content="Test Content",
        sources=[{
            "title": "Example Source",
            "url": "https://example.com",
            "snippet": "A test snippet",
            "domain": "example.com",
            "reliability_score": 1.0,
        }],
        execution_time_seconds=1.23,
    )
    assert summary.sources[0]["reliability_score"] == 1.0
    assert summary.sources[0]["title"] == "Example Source"

