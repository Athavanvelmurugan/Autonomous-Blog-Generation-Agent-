import asyncio
import logging
import asyncpg
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.config import get_settings
from backend.app.db.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()

from contextlib import asynccontextmanager

# Initialize High-Performance Async Engine for PostgreSQL (100x scale configuration)
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def ensure_database_exists():
    """
    Connects to PostgreSQL default 'postgres' database and verifies that
    the target database 'blog_db' exists. If not, it creates it automatically.
    """
    try:
        conn = await asyncpg.connect(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database="postgres",
        )
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", settings.DB_NAME
            )
            if not exists:
                logger.info(f"Database '{settings.DB_NAME}' does not exist. Creating...")
                await conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
                logger.info(f"Database '{settings.DB_NAME}' created successfully.")
            else:
                logger.info(f"Database '{settings.DB_NAME}' already exists.")
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Could not automatically verify/create database '{settings.DB_NAME}': {e}")


async def init_db():
    """
    Verifies database connectivity on application startup and ensures word count columns exist.
    """
    await ensure_database_exists()
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE blog_versions ADD COLUMN IF NOT EXISTS target_word_count INTEGER DEFAULT 800;"))
            await conn.execute(text("ALTER TABLE blog_versions ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;"))
            await conn.execute(text("ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS target_word_count INTEGER DEFAULT 800;"))
            await conn.execute(text("ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;"))
    except Exception as e:
        logger.warning(f"Could not auto-migrate word count columns: {e}")
    logger.info("PostgreSQL database connection verified.")


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Short-lived acquire-commit-release session context manager for LangGraph nodes
    and background jobs. Avoids connection hoarding across long LLM invocations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an active async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
