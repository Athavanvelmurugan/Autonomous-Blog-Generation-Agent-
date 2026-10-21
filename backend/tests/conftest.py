import sys
import asyncio
import pytest
from backend.app.db.database import engine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await engine.dispose()
