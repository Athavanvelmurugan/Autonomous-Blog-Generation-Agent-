import asyncio
import asyncpg
import json
from backend.app.config import get_settings

TOP_10_QUERIES = [
    (
        "1. Blog listing keyset pagination (active)",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, topic, status, created_at FROM blogs WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 20"
    ),
    (
        "2. Per-user blog feed",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, topic, status, created_at FROM blogs WHERE user_id = 1 AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 20"
    ),
    (
        "3. Blog search by topic prefix",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, topic, status FROM blogs WHERE topic LIKE 'Mastering%' AND deleted_at IS NULL LIMIT 20"
    ),
    (
        "4. Latest blog version lookup",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, blog_id, version_number, title FROM blog_versions WHERE blog_id = 1 ORDER BY version_number DESC LIMIT 1"
    ),
    (
        "5. Idempotent agent run lookup",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, idempotency_key, status FROM agent_runs WHERE idempotency_key = 'test-idemp-key-123'"
    ),
    (
        "6. Agent runs for a specific blog",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, status, total_execution_time_seconds, created_at FROM agent_runs WHERE blog_id = 1 ORDER BY created_at DESC"
    ),
    (
        "7. Stepped telemetry for a run",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, node_name, step_order, status, duration_seconds FROM run_steps WHERE run_id = 'test-run-id' ORDER BY step_order ASC"
    ),
    (
        "8. LLM metrics breakdown for a run",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, node_name, provider, model, total_tokens, latency_seconds FROM llm_calls WHERE run_id = 'test-run-id' ORDER BY created_at ASC"
    ),
    (
        "9. Verified sources lookup for a blog",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, title, url, domain FROM sources WHERE blog_id = 1"
    ),
    (
        "10. Fact-check audit retrieval for version",
        "EXPLAIN (ANALYZE, BUFFERS) SELECT id, score, passed, critique FROM fact_checks WHERE blog_version_id = 1"
    )
]

async def run_explains(label: str):
    settings = get_settings()
    conn = await asyncpg.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME
    )
    print(f"\n=======================================================")
    print(f" EXPLAIN ANALYZE BENCHMARK: {label}")
    print(f"=======================================================\n")
    results = []
    try:
        for title, sql in TOP_10_QUERIES:
            rows = await conn.fetch(sql)
            plan_lines = [r[0] for r in rows]
            # Extract execution time line
            exec_time_line = next((line for line in plan_lines if "Execution Time:" in line), plan_lines[-1])
            plan_summary = plan_lines[0]
            print(f"Query: {title}")
            print(f"  Plan: {plan_summary}")
            print(f"  {exec_time_line}\n")
            results.append({
                "query": title,
                "plan": plan_summary,
                "time": exec_time_line
            })
    finally:
        await conn.close()
    return results

if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "CURRENT"
    asyncio.run(run_explains(label))
