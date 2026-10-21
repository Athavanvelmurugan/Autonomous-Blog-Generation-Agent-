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
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print("Existing tables in blog_db:")
        for t in tables:
            print(" -", t["table_name"])
            
        has_blog_posts = any(t["table_name"] == "blog_posts" for t in tables)
        if has_blog_posts:
            count = await conn.fetchval("SELECT count(*) FROM blog_posts")
            print(f"Total rows in blog_posts: {count}")
            rows = await conn.fetch("SELECT id, topic, title, created_at FROM blog_posts LIMIT 5")
            for r in rows:
                print(f"   [ID {r['id']}] {r['title'][:40]}... ({r['topic']})")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
