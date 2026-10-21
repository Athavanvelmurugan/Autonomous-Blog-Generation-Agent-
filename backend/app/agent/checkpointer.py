import sys
import logging
from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from backend.app.config import get_settings
from backend.app.agent.graph import workflow

logger = logging.getLogger(__name__)

_pool: Optional[AsyncConnectionPool] = None
_checkpointer: Optional[AsyncPostgresSaver] = None
_checkpointed_graph = None

def get_postgres_conninfo() -> str:
    settings = get_settings()
    return f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

async def init_checkpointer():
    """
    Initializes PostgreSQL checkpointer pool and ensures checkpointer tables exist.
    """
    global _pool, _checkpointer, _checkpointed_graph
    try:
        conn_str = get_postgres_conninfo()
        _pool = AsyncConnectionPool(conninfo=conn_str, max_size=10, open=False)
        await _pool.open()
        _checkpointer = AsyncPostgresSaver(_pool)
        await _checkpointer.setup()
        _checkpointed_graph = workflow.compile(checkpointer=_checkpointer)
        logger.info("LangGraph PostgreSQL Checkpointer initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize PostgresSaver checkpointer: {e}. Falling back to in-memory workflow.")
        _checkpointed_graph = workflow.compile()

async def close_checkpointer():
    """Closes checkpointer connection pool gracefully on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

def get_graph():
    """Returns the compiled LangGraph workflow, using checkpointer if available."""
    global _checkpointed_graph
    if _checkpointed_graph is None:
        _checkpointed_graph = workflow.compile()
    return _checkpointed_graph
