import asyncio
import sys
from backend.app.config import get_settings

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def test_saver():
    settings = get_settings()
    conn_str = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    try:
        async with AsyncPostgresSaver.from_conn_string(conn_str) as checkpointer:
            await checkpointer.setup()
            print("AsyncPostgresSaver setup succeeded with WindowsSelectorEventLoopPolicy!")
    except Exception as e:
        print(f"AsyncPostgresSaver error: {e}")

if __name__ == "__main__":
    asyncio.run(test_saver())
