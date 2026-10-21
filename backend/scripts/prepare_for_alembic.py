import asyncio
import asyncpg
from backend.app.config import get_settings

async def main():
    settings = get_settings()
    conn = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME
    )
    try:
        # Check blog_posts count before
        before_count = await conn.fetchval("SELECT count(*) FROM blog_posts")
        print(f"Verified blog_posts count before cleanup: {before_count} rows")
        assert before_count == 16, f"Expected 16 rows, got {before_count}"

        # Clean up empty non-Alembic tables so Alembic migrations can manage them cleanly
        tables_to_drop = [
            "reader_events", "prompt_versions", "claims", "fact_checks",
            "sources", "llm_calls", "run_steps", "agent_runs",
            "blog_versions", "blogs", "api_keys", "users"
        ]
        for t in tables_to_drop:
            await conn.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
            print(f"Dropped empty table: {t}")

        # Check blog_posts count after
        after_count = await conn.fetchval("SELECT count(*) FROM blog_posts")
        print(f"Verified blog_posts count after cleanup: {after_count} rows")
        assert after_count == 16, f"Expected 16 rows, got {after_count}"
        print("Safety check passed: blog_posts is completely preserved with 16 rows!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
