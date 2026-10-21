import json
import uuid
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.db.models import AgentRun, RunStep

class RunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_run(
        self,
        idempotency_key: str,
        thread_id: str,
        blog_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[AgentRun, bool]:
        """
        Idempotent run initialization. If a run with this idempotency key already exists,
        it returns the existing record and is_created=False.
        """
        stmt = select(AgentRun).where(AgentRun.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing, False

        new_run = AgentRun(
            id=str(uuid.uuid4()),
            idempotency_key=idempotency_key,
            thread_id=thread_id,
            blog_id=blog_id,
            user_id=user_id,
            status="running",
        )
        try:
            self.session.add(new_run)
            await self.session.commit()
            await self.session.refresh(new_run)
            return new_run, True
        except Exception:
            await self.session.rollback()
            retry_res = await self.session.execute(stmt)
            winner = retry_res.scalar_one_or_none()
            if winner:
                return winner, False
            raise

    async def update_run_status(
        self,
        run_id: str,
        status: str,
        total_execution_time_seconds: float = 0.0,
        error_message: Optional[str] = None,
        blog_id: Optional[int] = None,
    ) -> Optional[AgentRun]:
        """
        Updates the final status, timing, and error details of an agent run.
        """
        stmt = select(AgentRun).where(AgentRun.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            return None

        run.status = status
        run.total_execution_time_seconds = total_execution_time_seconds
        if error_message:
            run.error_message = error_message
        if blog_id:
            run.blog_id = blog_id

        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def record_run_step(
        self,
        run_id: str,
        node_name: str,
        step_order: int,
        input_state: Optional[Dict[str, Any]] = None,
        output_state: Optional[Dict[str, Any]] = None,
        duration_seconds: float = 0.0,
        status: str = "completed",
    ) -> RunStep:
        """
        Records an atomic step execution within an agent DAG run.
        """
        step = RunStep(
            run_id=run_id,
            node_name=node_name,
            step_order=step_order,
            status=status,
            input_state_json=json.dumps(input_state) if input_state else None,
            output_state_json=json.dumps(output_state) if output_state else None,
            duration_seconds=duration_seconds,
        )
        self.session.add(step)
        await self.session.commit()
        await self.session.refresh(step)
        return step
