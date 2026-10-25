import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.orm import selectinload

from backend.app.db.models import Blog, BlogVersion, SourceDocument, BlogPost

class BlogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_blogs(
        self,
        cursor_created_at: Optional[datetime] = None,
        limit: int = 50,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[Blog], Optional[datetime]]:
        """
        Keyset-based cursor pagination for 100x scale.
        Avoids high-offset O(N) penalties.
        """
        query = (
            select(Blog)
            .options(
                selectinload(Blog.versions),
                selectinload(Blog.sources),
            )
            .order_by(desc(Blog.created_at))
            .limit(limit + 1)
        )

        filters = []
        if not include_deleted:
            filters.append(Blog.deleted_at.is_(None))

        if user_id is not None:
            filters.append(Blog.user_id == user_id)

        if cursor_created_at is not None:
            filters.append(Blog.created_at < cursor_created_at)

        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        blogs = list(result.scalars().all())

        next_cursor = None
        if len(blogs) > limit:
            extra = blogs.pop()
            next_cursor = blogs[-1].created_at if blogs else None

        return blogs, next_cursor

    async def get_blog_by_id(
        self,
        blog_id: int,
        user_id: Optional[int] = None,
        include_deleted: bool = False,
    ) -> Optional[Blog]:
        """
        Retrieves a single blog with latest version and sources.
        Enforces per-user access control if user_id is passed.
        """
        query = (
            select(Blog)
            .options(
                selectinload(Blog.versions),
                selectinload(Blog.sources),
            )
            .where(Blog.id == blog_id)
        )

        if not include_deleted:
            query = query.where(Blog.deleted_at.is_(None))

        if user_id is not None:
            query = query.where(Blog.user_id == user_id)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_blog_with_version(
        self,
        topic: str,
        tone: str,
        target_language: str,
        title: str,
        content: str,
        user_id: Optional[int] = None,
        verification_score: Optional[float] = 8.5,
        critique: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        original_title: Optional[str] = None,
        original_content: Optional[str] = None,
        execution_time_seconds: float = 0.0,
        steps_completed: Optional[List[str]] = None,
        target_word_count: Optional[int] = 800,
        word_count: Optional[int] = None,
    ) -> Blog:
        """
        Atomically creates a new Blog, its BlogVersion 1, and associated sources.
        Also writes to legacy BlogPost for 100% backward compatibility during rollout.
        """
        # 1. Create main Blog row
        new_blog = Blog(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            tone=tone or "Informative",
            target_language=target_language or "English",
            status="published",
        )
        self.session.add(new_blog)
        await self.session.flush()

        # 2. Create BlogVersion 1
        new_version = BlogVersion(
            blog_id=new_blog.id,
            version_number=1,
            title=title,
            content=content,
            original_title=original_title,
            original_content=original_content,
            target_word_count=target_word_count or 800,
            word_count=word_count or len(content.split()),
            verification_score=verification_score or 8.5,
            critique=critique,
            execution_time_seconds=execution_time_seconds,
            steps_completed_json=json.dumps(steps_completed or []),
        )
        self.session.add(new_version)
        await self.session.flush()

        new_blog.current_version_id = new_version.id

        # 3. Add sources
        if sources:
            for s in sources:
                if isinstance(s, dict) and s.get("url"):
                    src_doc = SourceDocument(
                        blog_id=new_blog.id,
                        title=s.get("title", "Untitled Source"),
                        url=s.get("url", ""),
                        snippet=s.get("snippet", ""),
                        domain=s.get("domain", ""),
                        reliability_score=s.get("reliability_score", 1.0),
                    )
                    self.session.add(src_doc)

        # 4. Backward compatibility dual-write to blog_posts
        try:
            legacy_post = BlogPost(
                id=new_blog.id,
                topic=topic,
                tone=tone,
                target_language=target_language,
                target_word_count=target_word_count or 800,
                word_count=word_count or len(content.split()),
                title=title,
                content=content,
                verification_score=verification_score or 8.5,
                critique=critique,
                original_title=original_title,
                original_content=original_content,
                execution_time_seconds=execution_time_seconds,
                steps_completed_json=json.dumps(steps_completed or []),
                sources_json=json.dumps(sources or []),
            )
            self.session.add(legacy_post)
        except Exception:
            pass

        await self.session.commit()
        return await self.get_blog_by_id(new_blog.id, user_id=user_id)

    async def update_blog(
        self,
        blog_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        user_id: Optional[int] = None,
        create_new_version: bool = False,
    ) -> Optional[Blog]:
        """
        Updates an existing blog. If create_new_version is True, preserves audit trail
        by creating a new BlogVersion row.
        """
        blog = await self.get_blog_by_id(blog_id, user_id=user_id)
        if not blog:
            return None

        latest = blog.latest_version
        if not latest:
            # Create a version if missing
            latest = BlogVersion(
                blog_id=blog.id,
                version_number=1,
                title=title or "Untitled",
                content=content or "",
            )
            self.session.add(latest)
            await self.session.flush()

        new_title = title.strip() if title and title.strip() else latest.title
        new_content = content if content is not None else latest.content

        if create_new_version:
            next_ver_num = (latest.version_number or 1) + 1
            new_version = BlogVersion(
                blog_id=blog.id,
                version_number=next_ver_num,
                title=new_title,
                content=new_content,
                original_title=latest.original_title,
                original_content=latest.original_content,
                verification_score=latest.verification_score,
                critique=latest.critique,
            )
            self.session.add(new_version)
            await self.session.flush()
            blog.current_version_id = new_version.id
        else:
            latest.title = new_title
            latest.content = new_content

        blog.updated_at = datetime.now(timezone.utc)

        # Update legacy blog_posts table if present
        legacy_res = await self.session.execute(select(BlogPost).where(BlogPost.id == blog_id))
        legacy = legacy_res.scalar_one_or_none()
        if legacy:
            legacy.title = new_title
            legacy.content = new_content

        await self.session.commit()
        return await self.get_blog_by_id(blog_id, user_id=user_id)

    async def delete_blog(
        self,
        blog_id: int,
        user_id: Optional[int] = None,
        hard_delete: bool = False,
    ) -> bool:
        """
        Deletes a blog. Defaults to soft delete (setting deleted_at).
        """
        blog = await self.get_blog_by_id(blog_id, user_id=user_id)
        if not blog:
            return False

        if hard_delete:
            await self.session.delete(blog)
            # Also remove legacy
            legacy_res = await self.session.execute(select(BlogPost).where(BlogPost.id == blog_id))
            legacy = legacy_res.scalar_one_or_none()
            if legacy:
                await self.session.delete(legacy)
        else:
            blog.deleted_at = datetime.now(timezone.utc)
            blog.status = "archived"

        await self.session.commit()
        return True
