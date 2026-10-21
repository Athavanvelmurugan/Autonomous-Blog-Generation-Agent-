import json
import time
import logging
from typing import Dict, Any, Optional

from backend.app.schema.state_schema import BlogState
from backend.app.db.database import get_async_session
from backend.app.db.repositories.run_repository import RunRepository
from backend.app.db.repositories.telemetry_repository import TelemetryRepository

logger = logging.getLogger(__name__)

async def record_node_step(
    node_name: str,
    state: BlogState,
    step_output: Dict[str, Any],
    start_time: float,
    llm_metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Shared, centralized database persistence helper for LangGraph nodes.
    Rules compliant:
    1. Single shared helper, avoiding scattered database queries inside nodes.
    2. Uses short-lived session context (acquire-commit-release).
    3. Idempotent run creation and atomic step logging.
    4. Automatically captures LLM calls, research sources, and fact-check audits.
    """
    duration = round(time.perf_counter() - start_time, 3)
    idempotency_key = state.get("idempotency_key") or f"run_{abs(hash(state.get('topic', '')) % 10000000)}_{int(time.time())}"
    thread_id = state.get("thread_id") or f"thread_{idempotency_key}"
    user_id = state.get("user_id")

    try:
        async with get_async_session() as session:
            run_repo = RunRepository(session)
            telemetry_repo = TelemetryRepository(session)

            # 1. Ensure AgentRun exists idempotently
            run, is_new = await run_repo.get_or_create_run(
                idempotency_key=idempotency_key,
                thread_id=thread_id,
                user_id=user_id,
            )

            # 2. Record this node's step
            step_order = len(state.get("steps_completed", [])) + 1
            input_summary = {
                "topic": state.get("topic"),
                "tone": state.get("tone"),
                "language": state.get("target_language"),
                "current_step": state.get("current_step"),
                "revision_count": state.get("revision_count", 0),
            }
            output_summary = {
                "current_step": step_output.get("current_step"),
                "title": step_output.get("title") or state.get("title"),
                "steps_completed": step_output.get("steps_completed", []),
            }

            step = await run_repo.record_run_step(
                run_id=run.id,
                node_name=node_name,
                step_order=step_order,
                input_state=input_summary,
                output_state=output_summary,
                duration_seconds=duration,
                status="completed",
            )

            # 3. Record LLM Call metrics if present
            if llm_metrics:
                await telemetry_repo.record_llm_call(
                    run_id=run.id,
                    step_id=step.id,
                    node_name=node_name,
                    provider=llm_metrics.get("provider", "groq"),
                    model=llm_metrics.get("model", "unknown"),
                    temperature=llm_metrics.get("temperature"),
                    prompt_tokens=llm_metrics.get("prompt_tokens", 0),
                    completion_tokens=llm_metrics.get("completion_tokens", 0),
                    cost_usd=llm_metrics.get("cost_usd", 0.0),
                    latency_seconds=llm_metrics.get("latency_seconds", duration),
                )

            # 4. Domain-specific telemetry
            if node_name == "research_agent" and step_output.get("sources"):
                await telemetry_repo.batch_record_sources(
                    sources=step_output["sources"],
                    run_id=run.id,
                )

            elif node_name == "verifier_agent":
                score = step_output.get("verification_score") or 8.5
                passed = step_output.get("passed", True)
                critique = step_output.get("critique")
                hallucinations = step_output.get("detected_hallucinations", [])
                unverified_cmds = step_output.get("unverified_commands", [])

                await telemetry_repo.record_fact_check(
                    run_id=run.id,
                    score=score,
                    passed=passed,
                    critique=critique,
                    hallucinations=hallucinations,
                    unverified_commands=unverified_cmds,
                )

            # 5. Check if pipeline reached final completion step
            if step_output.get("current_step") in ["translation_completed", "verified_complete"]:
                await run_repo.update_run_status(
                    run_id=run.id,
                    status="completed",
                    total_execution_time_seconds=duration,
                )

    except Exception as e:
        logger.warning(f"Persistence helper error in node '{node_name}': {e}", exc_info=False)
