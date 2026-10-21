import subprocess
import sys
import pytest
import asyncpg
from backend.app.config import get_settings

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def run_alembic_cmd(cmd_args):
    full_cmd = [sys.executable, "-m", "alembic"] + cmd_args
    res = subprocess.run(full_cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
    assert res.returncode == 0, f"Alembic command {' '.join(full_cmd)} failed:\n{res.stderr}\n{res.stdout}"
    return (res.stdout or "") + (res.stderr or "")

@pytest.mark.asyncio
async def test_migration_downgrade_and_upgrade():
    settings = get_settings()

    # 0. Ensure starting at head
    run_alembic_cmd(["upgrade", "head"])

    # 1. Downgrade to 0001_baseline
    downgrade_output = run_alembic_cmd(["downgrade", "0001_baseline"])
    assert "Running downgrade" in downgrade_output

    conn = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME
    )
    try:
        # Verify blog_posts still exists and has all rows preserved
        bp_count = await conn.fetchval("SELECT count(*) FROM blog_posts")
        assert bp_count >= 16, f"blog_posts lost data during downgrade! Count: {bp_count}"

        # Verify normalized tables dropped
        users_exist = await conn.fetchval("SELECT 1 FROM information_schema.tables WHERE table_name = 'users'")
        assert users_exist is None, "Table 'users' was not dropped on downgrade!"
    finally:
        await conn.close()

    # 2. Upgrade back to head
    upgrade_output = run_alembic_cmd(["upgrade", "head"])
    assert "Running upgrade" in upgrade_output

    conn2 = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME
    )
    try:
        # Verify tables recreated
        users_exist = await conn2.fetchval("SELECT 1 FROM information_schema.tables WHERE table_name = 'users'")
        assert users_exist == 1, "Table 'users' not created on upgrade!"

        # Re-run backfill to repopulate blogs for subsequent tests
        from backend.scripts.backfill_legacy_blogs import run_backfill
        await run_backfill()

        blogs_count = await conn2.fetchval("SELECT count(*) FROM blogs")
        assert blogs_count == bp_count, f"Mismatch: blogs has {blogs_count}, blog_posts has {bp_count}"
    finally:
        await conn2.close()
