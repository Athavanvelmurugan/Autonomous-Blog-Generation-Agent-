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
        tables = [
            "blog_posts", "users", "api_keys", "blogs", "blog_versions",
            "agent_runs", "run_steps", "llm_calls", "sources",
            "fact_checks", "claims", "prompt_versions", "reader_events",
            "alembic_version"
        ]
        for t in tables:
            exists = await conn.fetchval(
                "SELECT 1 FROM information_schema.tables WHERE table_name = $1", t
            )
            if exists:
                count = await conn.fetchval(f'SELECT count(*) FROM "{t}"')
                print(f"Table '{t}': {count} rows")
            else:
                print(f"Table '{t}': DOES NOT EXIST")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
