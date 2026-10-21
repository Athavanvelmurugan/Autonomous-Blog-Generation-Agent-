import asyncio
import uuid
import pytest
from backend.app.db.database import get_async_session
from backend.app.db.repositories import RunRepository, BlogRepository

@pytest.mark.asyncio
async def test_concurrent_idempotent_runs():
    """
    Launches 10 concurrent workers attempting to register the exact same idempotency key.
    Validates that exactly 1 run is created, with no duplicate keys or transaction deadlocks.
    """
    idemp_key = f"concurrent_idemp_{uuid.uuid4().hex}"
    thread_id = f"thread_{idemp_key}"

    async def worker(idx: int):
        async with get_async_session() as session:
            repo = RunRepository(session)
            run, is_new = await repo.get_or_create_run(
                idempotency_key=idemp_key,
                thread_id=thread_id
            )
            return run.id, is_new

    tasks = [worker(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    run_ids = set(r[0] for r in results)
    is_new_flags = [r[1] for r in results]

    # Exactly one run created
    assert len(run_ids) == 1
    assert is_new_flags.count(True) == 1
    assert is_new_flags.count(False) == 9


@pytest.mark.asyncio
async def test_concurrent_blog_creations_under_pool():
    """
    Verifies that 15 concurrent blog creation transactions execute successfully
    under the connection pool without exhaustion or timeout.
    """
    async def create_worker(idx: int):
        async with get_async_session() as session:
            repo = BlogRepository(session)
            blog = await repo.create_blog_with_version(
                topic=f"Concurrent Test Topic {idx} - {uuid.uuid4().hex[:6]}",
                tone="Informative",
                target_language="English",
                title=f"Concurrent Title {idx}",
                content=f"# Content {idx}",
            )
            return blog.id

    tasks = [create_worker(i) for i in range(15)]
    blog_ids = await asyncio.gather(*tasks)

    assert len(blog_ids) == 15
    assert len(set(blog_ids)) == 15

    # Cleanup created blogs
    for bid in blog_ids:
        async with get_async_session() as session:
            repo = BlogRepository(session)
            await repo.delete_blog(bid, hard_delete=True)
