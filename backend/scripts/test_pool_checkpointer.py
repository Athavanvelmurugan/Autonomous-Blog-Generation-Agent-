import asyncio
import sys
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from backend.app.config import get_settings
from backend.app.agent.graph import workflow

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_pooled_checkpointer():
    settings = get_settings()
    conn_str = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    
    async with AsyncConnectionPool(conninfo=conn_str, max_size=10, open=False) as pool:
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        app_graph = workflow.compile(checkpointer=checkpointer)
        print("Successfully compiled StateGraph with AsyncPostgresSaver checkpointer!")

if __name__ == "__main__":
    asyncio.run(test_pooled_checkpointer())
