import json
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.models import LLMCall, SourceDocument, FactCheck, Claim

class TelemetryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_llm_call(
        self,
        node_name: str,
        provider: str,
        model: str,
        run_id: Optional[str] = None,
        step_id: Optional[int] = None,
        temperature: Optional[float] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_seconds: float = 0.0,
    ) -> LLMCall:
        """
        Logs individual LLM inference metrics (tokens, latency, estimated cost).
        """
        total_tokens = prompt_tokens + completion_tokens
        call = LLMCall(
            run_id=run_id,
            step_id=step_id,
            node_name=node_name,
            provider=provider,
            model=model,
            temperature=temperature,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_seconds=latency_seconds,
        )
        self.session.add(call)
        await self.session.commit()
        await self.session.refresh(call)
        return call

    async def batch_record_sources(
        self,
        sources: List[Dict[str, Any]],
        run_id: Optional[str] = None,
        blog_id: Optional[int] = None,
    ) -> List[SourceDocument]:
        """
        Persists ground-truth research sources and citations.
        """
        created = []
        for s in sources:
            if not isinstance(s, dict) or not s.get("url"):
                continue
            doc = SourceDocument(
                run_id=run_id,
                blog_id=blog_id,
                title=s.get("title", "Untitled Source"),
                url=s.get("url", ""),
                snippet=s.get("snippet", ""),
                domain=s.get("domain", ""),
                reliability_score=s.get("reliability_score", 1.0),
            )
            self.session.add(doc)
            created.append(doc)

        if created:
            await self.session.commit()
            for doc in created:
                await self.session.refresh(doc)
        return created

    async def record_fact_check(
        self,
        score: float,
        passed: bool,
        critique: Optional[str] = None,
        run_id: Optional[str] = None,
        blog_version_id: Optional[int] = None,
        hallucinations: Optional[List[str]] = None,
        unverified_commands: Optional[List[str]] = None,
        claims: Optional[List[Dict[str, Any]]] = None,
    ) -> FactCheck:
        """
        Stores fact-check audit results, verification flags, and audited claims.
        """
        fc = FactCheck(
            run_id=run_id,
            blog_version_id=blog_version_id,
            score=score,
            passed=passed,
            critique=critique,
            hallucinations_json=json.dumps(hallucinations or []),
            unverified_commands_json=json.dumps(unverified_commands or []),
        )
        self.session.add(fc)
        await self.session.flush()

        if claims:
            for c in claims:
                claim_obj = Claim(
                    fact_check_id=fc.id,
                    claim_text=c.get("claim_text", ""),
                    status=c.get("status", "verified"),
                    evidence=c.get("evidence", ""),
                )
                self.session.add(claim_obj)

        await self.session.commit()
        await self.session.refresh(fc)
        return fc
