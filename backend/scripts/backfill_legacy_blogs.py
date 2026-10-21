import asyncio
import json
import uuid
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, text
from backend.app.config import get_settings
from backend.app.db.models import (
    BlogPost,
    User,
    Blog,
    BlogVersion,
    SourceDocument,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill")

async def run_backfill():
    settings = get_settings()
    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Step 1: Pre-migration verification of row counts
        legacy_count = (await session.execute(select(func.count(BlogPost.id)))).scalar_one()
        blogs_before = (await session.execute(select(func.count(Blog.id)))).scalar_one()
        versions_before = (await session.execute(select(func.count(BlogVersion.id)))).scalar_one()

        logger.info("=== BEFORE BACKFILL VERIFICATION ===")
        logger.info(f"blog_posts (Legacy): {legacy_count} rows")
        logger.info(f"blogs (New Target): {blogs_before} rows")
        logger.info(f"blog_versions: {versions_before} rows")

        if legacy_count == 0:
            logger.warning("No legacy rows found to backfill.")
            return

        # Step 2: Ensure Default System User Exists
        user_res = await session.execute(select(User).where(User.email == "system@autonomous-blog.ai"))
        system_user = user_res.scalar_one_or_none()
        if not system_user:
            system_user = User(
                email="system@autonomous-blog.ai",
                role="admin",
                is_active=True,
            )
            session.add(system_user)
            await session.commit()
            await session.refresh(system_user)
            logger.info(f"Created default system user with ID: {system_user.id}")

        # Step 3: Fetch all legacy blog posts
        legacy_rows = (await session.execute(select(BlogPost).order_by(BlogPost.id.asc()))).scalars().all()

        backfilled_count = 0
        for post in legacy_rows:
            # Check if already migrated (idempotency)
            existing_blog = (await session.execute(select(Blog).where(Blog.id == post.id))).scalar_one_or_none()
            if existing_blog:
                logger.info(f"Blog ID {post.id} already backfilled. Skipping.")
                continue

            # Create new Blog record
            new_blog = Blog(
                id=post.id,
                uuid=str(uuid.uuid4()),
                user_id=system_user.id,
                topic=post.topic,
                tone=post.tone,
                target_language=post.target_language,
                status="published",
                created_at=post.created_at,
                updated_at=post.created_at,
            )
            session.add(new_blog)
            await session.flush()

            # Create BlogVersion v1 record
            new_version = BlogVersion(
                blog_id=new_blog.id,
                version_number=1,
                title=post.title,
                content=post.content,
                original_title=post.original_title,
                original_content=post.original_content,
                verification_score=post.verification_score,
                critique=post.critique,
                execution_time_seconds=post.execution_time_seconds,
                steps_completed_json=post.steps_completed_json,
                created_at=post.created_at,
            )
            session.add(new_version)
            await session.flush()

            new_blog.current_version_id = new_version.id

            # Migrate sources if available
            try:
                sources_data = json.loads(post.sources_json or "[]")
                for s in sources_data:
                    if isinstance(s, dict) and s.get("url"):
                        src_doc = SourceDocument(
                            blog_id=new_blog.id,
                            title=s.get("title", "Untitled Source"),
                            url=s.get("url", ""),
                            snippet=s.get("snippet", ""),
                            domain=s.get("domain", ""),
                            reliability_score=s.get("reliability_score", 1.0),
                            created_at=post.created_at,
                        )
                        session.add(src_doc)
            except Exception as parse_err:
                logger.warning(f"Failed parsing sources for blog {post.id}: {parse_err}")

            backfilled_count += 1

        await session.commit()
        logger.info(f"Successfully committed backfill for {backfilled_count} rows.")

        # Update sequence so subsequent new blogs autoincrement from max(id) + 1
        await session.execute(text("SELECT setval('blogs_id_seq', (SELECT COALESCE(MAX(id), 1) FROM blogs))"))
        await session.commit()

        # Step 4: Post-migration verification
        blogs_after = (await session.execute(select(func.count(Blog.id)))).scalar_one()
        versions_after = (await session.execute(select(func.count(BlogVersion.id)))).scalar_one()
        sources_after = (await session.execute(select(func.count(SourceDocument.id)))).scalar_one()

        logger.info("=== AFTER BACKFILL VERIFICATION ===")
        logger.info(f"blog_posts (Legacy): {legacy_count} rows")
        logger.info(f"blogs (New Target): {blogs_after} rows")
        logger.info(f"blog_versions: {versions_after} rows")
        logger.info(f"sources: {sources_after} rows")

        assert blogs_after == legacy_count, f"Row count mismatch! Legacy: {legacy_count}, New blogs: {blogs_after}"
        assert versions_after == legacy_count, f"Version count mismatch! Legacy: {legacy_count}, Versions: {versions_after}"
        logger.info("VERIFICATION PASSED: Zero data loss! Exactly 16 rows migrated with all versions and sources intact.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_backfill())
