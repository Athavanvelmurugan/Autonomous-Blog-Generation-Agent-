import sys
import json
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.app.config import get_settings
from backend.app.db.database import init_db, get_db, get_async_session
from backend.app.db.models import ReaderEvent
from backend.app.db.repositories import BlogRepository, UserRepository
from backend.app.schema.state_schema import BlogState
from backend.app.schema.api_schema import (
    BlogGenerationRequest,
    BlogGenerationResponse,
    BlogPostSummary,
    BlogPostUpdateRequest,
    LanguageOption,
    ReaderEventCreateRequest,
)
from backend.app.agent.checkpointer import init_checkpointer, close_checkpointer, get_graph
from backend.app.core.cache import cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    Initializes database connectivity and LangGraph checkpointer.
    """
    logger.info("Initializing Autonomous Blog Generation Engine...")
    try:
        await init_db()
        await init_checkpointer()
    except Exception as e:
        logger.error(f"Startup initialization warning: {e}")
    yield
    logger.info("Shutting down Autonomous Blog Generation Engine...")
    try:
        await close_checkpointer()
    except Exception as e:
        logger.warning(f"Shutdown cleanup warning: {e}")


app = FastAPI(
    title="Autonomous Blog Generation Engine",
    description="Multi-Agent Directed Acyclic Graph (DAG) with Real-Time Web Research & Fact Verification",
    version="1.2.0",
    lifespan=lifespan,
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES: List[LanguageOption] = [
    LanguageOption(code="en", name="English", native_name="English"),
    LanguageOption(code="es", name="Spanish", native_name="Español"),
    LanguageOption(code="fr", name="French", native_name="Français"),
    LanguageOption(code="de", name="German", native_name="Deutsch"),
    LanguageOption(code="hi", name="Hindi", native_name="हिन्दी"),
    LanguageOption(code="ja", name="Japanese", native_name="日本語"),
    LanguageOption(code="pt", name="Portuguese", native_name="Português"),
    LanguageOption(code="it", name="Italian", native_name="Italiano"),
    LanguageOption(code="zh", name="Chinese", native_name="中文"),
]


async def get_optional_user_id(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> Optional[int]:
    """Resolves authenticated user ID from API key for multi-tenant isolation."""
    if not x_api_key:
        return None
    user_repo = UserRepository(db)
    user = await user_repo.validate_api_key(x_api_key)
    return user.id if user else None


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health probe returning server status and active LLM configuration."""
    return {
        "status": "healthy",
        "service": "Autonomous Blog Generation Engine",
        "model_provider": settings.MODEL_PROVIDER,
        "model_name": settings.MODEL_NAME,
        "database": settings.DB_NAME,
        "langsmith_tracing": settings.LANGSMITH_TRACING,
        "checkpointer": "PostgresSaver (Async)",
        "features": ["trend_research_agent", "fact_verifier_agent", "self_correction_loop", "100x_db_layer"],
    }


@app.get("/api/languages", response_model=List[LanguageOption], tags=["Blog Engine"])
async def get_languages():
    """Retrieve the list of supported output languages for blog generation."""
    cached = cache.get("languages:supported")
    if cached:
        return cached
    cache.set("languages:supported", SUPPORTED_LANGUAGES, ttl_seconds=3600)
    return SUPPORTED_LANGUAGES


@app.post("/api/generate-blog", response_model=BlogGenerationResponse, tags=["Blog Engine"])
async def generate_blog(
    request: BlogGenerationRequest,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes the 5-Stage multi-agent LangGraph workflow with transactional persistence,
    idempotent deduplication, and connection-pooled Postgres checkpointer.
    """
    start_time = time.perf_counter()
    logger.info(f"Received blog generation request: topic='{request.topic}', language='{request.target_language}'")

    # Idempotency and thread isolation
    idempotency_key = request.idempotency_key or f"run_{abs(hash(request.topic)) % 10000000}_{int(time.time())}"
    thread_id = f"thread_{idempotency_key}"

    initial_state: BlogState = {
        "topic": request.topic.strip(),
        "tone": request.tone or "Informative",
        "target_language": request.target_language or "English",
        "creativity": request.creativity or "balanced",
        "planned_queries": [],
        "query_retry_count": 0,
        "raw_sources": [],
        "deduped_sources": [],
        "sources": [],
        "facts": [],
        "today_date": None,
        "topic_type": None,
        "category": None,
        "research_data": None,
        "title": "",
        "content": "",
        "sources_section": None,
        "verification_score": None,
        "passed": None,
        "critique": None,
        "detected_hallucinations": [],
        "unverified_commands": [],
        "verification_report": None,
        "revision_count": 0,
        "review_fallback_action": None,
        "original_title": None,
        "original_content": None,
        "translated_title": None,
        "translated_content": None,
        "current_step": "started",
        "steps_completed": [],
        "node_timings": {},
        "error": None,
        "run_id": None,
        "idempotency_key": idempotency_key,
        "thread_id": thread_id,
        "user_id": user_id,
    }

    try:
        app_graph = get_graph()
        # Asynchronously invoke the LangGraph DAG with checkpoint thread_id
        final_state: BlogState = await app_graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}}
        )

        # Check for explicit failure path (e.g. insufficient sources or verification halt)
        if final_state.get("error") or final_state.get("current_step") == "failed":
            err_msg = final_state.get("error") or "Pipeline halted: requirements not met."
            logger.warning(f"Blog generation aborted: {err_msg}")
            if "insufficient" in err_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=err_msg
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )

        execution_time = round(time.perf_counter() - start_time, 2)
        verif_score = final_state.get("verification_score") or 8.5
        critique_text = final_state.get("critique")
        retrieved_sources = final_state.get("sources", [])

        # Transactional write through BlogRepository
        blog_repo = BlogRepository(db)
        saved_blog = await blog_repo.create_blog_with_version(
            topic=request.topic,
            tone=request.tone or "Informative",
            target_language=request.target_language or "English",
            title=final_state["title"],
            content=final_state["content"],
            user_id=user_id,
            verification_score=verif_score,
            critique=critique_text,
            sources=retrieved_sources,
            original_title=final_state.get("original_title"),
            original_content=final_state.get("original_content"),
            execution_time_seconds=execution_time,
            steps_completed=final_state.get("steps_completed", []),
        )

        # Invalidate listing cache
        cache.invalidate_prefix("blogs:")

        return BlogGenerationResponse(
            id=saved_blog.id,
            status="success",
            topic=request.topic,
            tone=request.tone or "Informative",
            language=request.target_language or "English",
            title=final_state["title"],
            content=final_state["content"],
            verification_score=verif_score,
            critique=critique_text,
            sources=retrieved_sources,
            original_title=final_state.get("original_title"),
            original_content=final_state.get("original_content"),
            execution_time_seconds=execution_time,
            steps_completed=final_state.get("steps_completed", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during blog generation pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blog generation agent encountered an error: {str(e)}"
        )


@app.post("/api/generate-blog/stream", tags=["Blog Engine"])
async def generate_blog_stream(
    request: BlogGenerationRequest,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Streaming SSE endpoint providing real-time multi-agent execution telemetry:
    Emits events as each agent node completes, and yields the final verified blog upon completion.
    """
    start_time = time.perf_counter()
    logger.info(f"Received streaming blog generation request: topic='{request.topic}'")

    idempotency_key = request.idempotency_key or f"run_{abs(hash(request.topic)) % 10000000}_{int(time.time())}"
    thread_id = f"thread_{idempotency_key}"

    initial_state: BlogState = {
        "topic": request.topic.strip(),
        "tone": request.tone or "Informative",
        "target_language": request.target_language or "English",
        "creativity": request.creativity or "balanced",
        "topic_type": None,
        "category": None,
        "today_date": None,
        "planned_queries": [],
        "query_retry_count": 0,
        "raw_sources": [],
        "deduped_sources": [],
        "facts": [],
        "research_data": None,
        "sources": [],
        "title": "",
        "content": "",
        "sources_section": None,
        "verification_score": None,
        "passed": None,
        "critique": None,
        "detected_hallucinations": [],
        "unverified_commands": [],
        "verification_report": None,
        "revision_count": 0,
        "review_fallback_action": None,
        "original_title": None,
        "original_content": None,
        "translated_title": None,
        "translated_content": None,
        "current_step": "started",
        "steps_completed": [],
        "node_timings": {},
        "error": None,
        "run_id": None,
        "idempotency_key": idempotency_key,
        "thread_id": thread_id,
        "user_id": user_id,
    }

    async def event_generator():
        accumulated_state = dict(initial_state)
        try:
            yield f"data: {json.dumps({'type': 'step_start', 'node': 'plan_queries', 'message': 'Planning search queries and temporal keywords...'})}\n\n"
            
            app_graph = get_graph()
            async for output in app_graph.astream(
                initial_state,
                stream_mode="updates",
                config={"configurable": {"thread_id": thread_id}}
            ):
                for node_name, node_update in output.items():
                    accumulated_state.update(node_update)
                    
                    event_data = {
                        "type": "node_update",
                        "node": node_name,
                        "current_step": node_update.get("current_step"),
                        "steps_completed": accumulated_state.get("steps_completed", []),
                        "title": accumulated_state.get("title"),
                        "revision_count": accumulated_state.get("revision_count", 0),
                    }
                    
                    if node_name == "plan_queries":
                        event_data["message"] = f"Generated {len(node_update.get('planned_queries', []))} search queries (Type: {node_update.get('topic_type', 'trending')})."
                    elif node_name == "collect":
                        event_data["message"] = f"Ingested candidate articles across multi-sources."
                    elif node_name == "clean_dedupe":
                        sources = node_update.get("deduped_sources", [])
                        domains = len({s.get('domain') for s in sources if s.get('domain')})
                        event_data["sources"] = sources
                        event_data["message"] = f"Deduplicated to {len(sources)} verified sources across {domains} domains."
                    elif node_name == "extract_facts":
                        facts = node_update.get("facts", [])
                        event_data["facts"] = facts
                        event_data["message"] = f"Extracted and verified {len(facts)} atomic facts with verbatim evidence."
                    elif node_name == "title_generator":
                        event_data["title"] = node_update.get("title")
                        event_data["message"] = f"Headline generated: {node_update.get('title')}"
                    elif node_name == "content_generator":
                        event_data["message"] = f"Blog draft synthesized ({len(node_update.get('content', '').split())} words) with inline citations."
                        event_data["content_preview"] = node_update.get("content", "")[:300]
                    elif node_name == "verifier_agent":
                        score = node_update.get("verification_score")
                        passed = node_update.get("passed", True)
                        event_data["verification_score"] = score
                        event_data["passed"] = passed
                        event_data["critique"] = node_update.get("critique")
                        status_str = "PASSED" if passed else "REVISING"
                        event_data["message"] = f"Verification {status_str}: {score}/10."
                    elif node_name == "translator":
                        event_data["message"] = f"Localized into {request.target_language}."
                    elif node_name == "fail_node":
                        event_data["type"] = "error"
                        err_text = node_update.get("error", "Pipeline terminated due to quality constraints.")
                        event_data["detail"] = err_text
                        event_data["message"] = err_text
                    
                    yield f"data: {json.dumps(event_data)}\n\n"

            # Check if workflow aborted due to error
            if accumulated_state.get("error") or accumulated_state.get("current_step") == "failed":
                err_msg = accumulated_state.get("error") or "Pipeline halted: requirements not met."
                logger.warning(f"[SSE Stream] Pipeline terminated with error: {err_msg}")
                yield f"data: {json.dumps({'type': 'error', 'detail': err_msg})}\n\n"
                return

            # Workflow completed: persist via BlogRepository and emit final event
            execution_time = round(time.perf_counter() - start_time, 2)
            verif_score = accumulated_state.get("verification_score") or 8.5
            critique_text = accumulated_state.get("critique")
            retrieved_sources = accumulated_state.get("sources", [])

            saved_id = None
            try:
                blog_repo = BlogRepository(db)
                saved_blog = await blog_repo.create_blog_with_version(
                    topic=request.topic,
                    tone=request.tone or "Informative",
                    target_language=request.target_language or "English",
                    title=accumulated_state["title"],
                    content=accumulated_state["content"],
                    user_id=user_id,
                    verification_score=verif_score,
                    critique=critique_text,
                    sources=retrieved_sources,
                    original_title=accumulated_state.get("original_title"),
                    original_content=accumulated_state.get("original_content"),
                    execution_time_seconds=execution_time,
                    steps_completed=accumulated_state.get("steps_completed", []),
                )
                saved_id = saved_blog.id
                cache.invalidate_prefix("blogs:")
                logger.info(f"Saved streaming verified blog post to PostgreSQL with ID: {saved_id}")
            except Exception as db_err:
                logger.warning(f"Failed to persist streaming blog: {db_err}")

            final_blog = {
                "id": saved_id,
                "status": "success",
                "topic": request.topic,
                "tone": request.tone,
                "language": request.target_language,
                "title": accumulated_state["title"],
                "content": accumulated_state["content"],
                "verification_score": verif_score,
                "critique": critique_text,
                "sources": retrieved_sources,
                "original_title": accumulated_state.get("original_title"),
                "original_content": accumulated_state.get("original_content"),
                "execution_time_seconds": execution_time,
                "steps_completed": accumulated_state.get("steps_completed", []),
            }

            yield f"data: {json.dumps({'type': 'complete', 'blog': final_blog})}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/api/blogs", response_model=List[BlogPostSummary], tags=["History"])
async def list_blogs(
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve saved blog generation history using keyset pagination and caching."""
    cache_key = f"blogs:list:{user_id or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        blog_repo = BlogRepository(db)
        blogs, _ = await blog_repo.list_blogs(limit=50, user_id=user_id)
        results = [
            BlogPostSummary(
                id=b.id,
                topic=b.topic,
                tone=b.tone,
                target_language=b.target_language,
                title=b.latest_version.title if b.latest_version else "",
                content=b.latest_version.content if b.latest_version else "",
                verification_score=b.latest_version.verification_score if b.latest_version else 8.5,
                critique=b.latest_version.critique if b.latest_version else None,
                sources=[s.to_dict() for s in b.sources] if b.sources else [],
                original_title=b.latest_version.original_title if b.latest_version else None,
                original_content=b.latest_version.original_content if b.latest_version else None,
                execution_time_seconds=b.latest_version.execution_time_seconds if b.latest_version else 0.0,
                created_at=b.created_at.isoformat() if b.created_at else None,
            )
            for b in blogs
        ]
        cache.set(cache_key, results, ttl_seconds=30)
        return results
    except Exception as e:
        logger.warning(f"Could not load blog history from database: {e}")
        return []


@app.get("/api/blogs/{blog_id}", response_model=BlogPostSummary, tags=["History"])
async def get_blog_by_id(
    blog_id: int,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a single blog post by its primary key ID with read caching."""
    cache_key = f"blogs:{blog_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    blog_repo = BlogRepository(db)
    post = await blog_repo.get_blog_by_id(blog_id, user_id=user_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    latest = post.latest_version
    result = BlogPostSummary(
        id=post.id,
        topic=post.topic,
        tone=post.tone,
        target_language=post.target_language,
        title=latest.title if latest else "",
        content=latest.content if latest else "",
        verification_score=latest.verification_score if latest else 8.5,
        critique=latest.critique if latest else None,
        sources=[s.to_dict() for s in post.sources] if post.sources else [],
        original_title=latest.original_title if latest else None,
        original_content=latest.original_content if latest else None,
        execution_time_seconds=latest.execution_time_seconds if latest else 0.0,
        created_at=post.created_at.isoformat() if post.created_at else None,
    )
    cache.set(cache_key, result, ttl_seconds=300)
    return result


@app.delete("/api/blogs/{blog_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["History"])
async def delete_blog(
    blog_id: int,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog record from PostgreSQL (soft-delete with cache invalidation)."""
    blog_repo = BlogRepository(db)
    success = await blog_repo.delete_blog(blog_id, user_id=user_id, hard_delete=False)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    cache.invalidate_prefix("blogs:")
    return None


@app.put("/api/blogs/{blog_id}", response_model=BlogPostSummary, tags=["History"])
async def update_blog(
    blog_id: int,
    request: BlogPostUpdateRequest,
    user_id: Optional[int] = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing blog post's title or content in PostgreSQL with versioning."""
    blog_repo = BlogRepository(db)
    post = await blog_repo.update_blog(
        blog_id=blog_id,
        title=request.title,
        content=request.content,
        user_id=user_id,
        create_new_version=False,
    )
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    cache.invalidate_prefix("blogs:")
    latest = post.latest_version
    return BlogPostSummary(
        id=post.id,
        topic=post.topic,
        tone=post.tone,
        target_language=post.target_language,
        title=latest.title if latest else "",
        content=latest.content if latest else "",
        verification_score=latest.verification_score if latest else 8.5,
        critique=latest.critique if latest else None,
        sources=[s.to_dict() for s in post.sources] if post.sources else [],
        original_title=latest.original_title if latest else None,
        original_content=latest.original_content if latest else None,
        execution_time_seconds=latest.execution_time_seconds if latest else 0.0,
        created_at=post.created_at.isoformat() if post.created_at else None,
    )


@app.post("/api/blogs/{blog_id}/events", status_code=status.HTTP_201_CREATED, tags=["Analytics"])
async def track_reader_event(
    blog_id: int,
    event: ReaderEventCreateRequest,
    background_tasks: BackgroundTasks,
):
    """Track reader engagement events asynchronously in the background."""
    async def record_event():
        try:
            async with get_async_session() as session:
                ev = ReaderEvent(
                    blog_id=blog_id,
                    event_type=event.event_type,
                    metadata_json=json.dumps(event.metadata or {}),
                )
                session.add(ev)
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to record reader event: {e}")

    background_tasks.add_task(record_event)
    return {"status": "recorded"}
