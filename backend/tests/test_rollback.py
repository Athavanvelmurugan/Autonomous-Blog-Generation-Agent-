import uuid
import pytest
from sqlalchemy import select
from backend.app.db.database import get_async_session
from backend.app.db.models import Blog, BlogVersion

@pytest.mark.asyncio
async def test_atomic_transaction_rollback_on_failure():
    """
    Tests that a multi-step transaction that encounters an unhandled exception
    cleanly rolls back, leaving no orphaned Blog or BlogVersion rows.
    """
    test_uuid = str(uuid.uuid4())
    unique_topic = f"Rollback Test {test_uuid[:8]}"

    try:
        async with get_async_session() as session:
            # 1. Insert Blog
            blog = Blog(
                uuid=test_uuid,
                topic=unique_topic,
                tone="Technical",
                target_language="English",
            )
            session.add(blog)
            await session.flush()

            # 2. Insert Version
            version = BlogVersion(
                blog_id=blog.id,
                version_number=1,
                title="Rollback Title",
                content="Rollback Content",
            )
            session.add(version)
            await session.flush()

            # 3. Simulate unexpected failure before commit
            raise RuntimeError("Simulated crash during node execution!")

            await session.commit()
    except RuntimeError:
        pass  # Expected exception

    # 4. Verify that neither the Blog nor the BlogVersion was persisted
    async with get_async_session() as verify_session:
        res_blog = await verify_session.execute(select(Blog).where(Blog.uuid == test_uuid))
        assert res_blog.scalar_one_or_none() is None, "Blog record was committed despite transaction failure!"

        res_ver = await verify_session.execute(select(BlogVersion).where(BlogVersion.title == "Rollback Title"))
        assert res_ver.scalar_one_or_none() is None, "BlogVersion was orphaned after transaction crash!"
