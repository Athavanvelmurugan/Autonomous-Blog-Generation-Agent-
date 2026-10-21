import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ==========================================
# 0. Legacy Model (Retained for Backward Compatibility & Zero-Downtime Backfill)
# ==========================================
class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic = Column(String(300), nullable=False, index=True)
    tone = Column(String(50), nullable=False, default="Informative")
    target_language = Column(String(50), nullable=False, default="English")
    
    # Final localized or generated output
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)

    # Verification & Quality Audit
    verification_score = Column(Float, default=8.5)
    critique = Column(Text, nullable=True)

    # Live Sources & Citations
    sources_json = Column(Text, default="[]")

    # Original English output if translated
    original_title = Column(Text, nullable=True)
    original_content = Column(Text, nullable=True)

    execution_time_seconds = Column(Float, default=0.0)
    steps_completed_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def steps_completed(self) -> List[str]:
        try:
            return json.loads(self.steps_completed_json or "[]")
        except Exception:
            return []

    @steps_completed.setter
    def steps_completed(self, steps: List[str]):
        self.steps_completed_json = json.dumps(steps)

    @property
    def sources(self) -> List[Dict[str, str]]:
        try:
            return json.loads(self.sources_json or "[]")
        except Exception:
            return []

    @sources.setter
    def sources(self, srcs: List[Dict[str, str]]):
        self.sources_json = json.dumps(srcs)

    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "tone": self.tone,
            "target_language": self.target_language,
            "title": self.title,
            "content": self.content,
            "verification_score": self.verification_score,
            "critique": self.critique,
            "sources": self.sources,
            "original_title": self.original_title,
            "original_content": self.original_content,
            "execution_time_seconds": self.execution_time_seconds,
            "steps_completed": self.steps_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==========================================
# 1. Identity & Multi-Tenancy Layer
# ==========================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default="user")  # 'admin', 'editor', 'user'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    blogs = relationship("Blog", back_populates="user")
    agent_runs = relationship("AgentRun", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, default="default")
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="api_keys")


# ==========================================
# 2. Content & Versioning Domain
# ==========================================
class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    topic = Column(String(300), nullable=False, index=True)
    tone = Column(String(50), nullable=False, default="Informative")
    target_language = Column(String(50), nullable=False, default="English")
    status = Column(String(50), nullable=False, default="published", index=True)  # 'draft', 'published', 'archived'
    current_version_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="blogs")
    versions = relationship("BlogVersion", back_populates="blog", cascade="all, delete-orphan", order_by="desc(BlogVersion.version_number)")
    sources = relationship("SourceDocument", back_populates="blog", cascade="all, delete-orphan")
    reader_events = relationship("ReaderEvent", back_populates="blog", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="blog")

    @property
    def latest_version(self) -> Optional["BlogVersion"]:
        if self.versions:
            return self.versions[0]
        return None

    def to_summary_dict(self):
        latest = self.latest_version
        return {
            "id": self.id,
            "uuid": self.uuid,
            "topic": self.topic,
            "tone": self.tone,
            "target_language": self.target_language,
            "title": latest.title if latest else "",
            "content": latest.content if latest else "",
            "verification_score": latest.verification_score if latest else 8.5,
            "critique": latest.critique if latest else None,
            "sources": [s.to_dict() for s in self.sources] if self.sources else [],
            "original_title": latest.original_title if latest else None,
            "original_content": latest.original_content if latest else None,
            "execution_time_seconds": latest.execution_time_seconds if latest else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BlogVersion(Base):
    __tablename__ = "blog_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    original_title = Column(Text, nullable=True)
    original_content = Column(Text, nullable=True)
    verification_score = Column(Float, nullable=True, default=8.5)
    critique = Column(Text, nullable=True)
    execution_time_seconds = Column(Float, default=0.0)
    steps_completed_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    blog = relationship("Blog", back_populates="versions")
    fact_checks = relationship("FactCheck", back_populates="blog_version", cascade="all, delete-orphan")

    @property
    def steps_completed(self) -> List[str]:
        try:
            return json.loads(self.steps_completed_json or "[]")
        except Exception:
            return []

    @steps_completed.setter
    def steps_completed(self, steps: List[str]):
        self.steps_completed_json = json.dumps(steps)


# ==========================================
# 3. Agent Execution & Orchestration Observability
# ==========================================
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    thread_id = Column(String(128), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    total_execution_time_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    blog = relationship("Blog", back_populates="agent_runs")
    user = relationship("User", back_populates="agent_runs")
    steps = relationship("RunStep", back_populates="run", cascade="all, delete-orphan", order_by="RunStep.step_order")
    llm_calls = relationship("LLMCall", back_populates="run", cascade="all, delete-orphan")
    sources = relationship("SourceDocument", back_populates="run", cascade="all, delete-orphan")
    fact_checks = relationship("FactCheck", back_populates="run", cascade="all, delete-orphan")


class RunStep(Base):
    __tablename__ = "run_steps"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    node_name = Column(String(100), nullable=False, index=True)
    step_order = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="completed")  # running, completed, failed
    input_state_json = Column(Text, nullable=True)
    output_state_json = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run = relationship("AgentRun", back_populates="steps")
    llm_calls = relationship("LLMCall", back_populates="step")


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    step_id = Column(Integer, ForeignKey("run_steps.id", ondelete="SET NULL"), nullable=True, index=True)
    node_name = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    run = relationship("AgentRun", back_populates="llm_calls")
    step = relationship("RunStep", back_populates="llm_calls")


# ==========================================
# 4. Citations, Verification & Claims Domain
# ==========================================
class SourceDocument(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(String(2048), nullable=False)
    snippet = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    reliability_score = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run = relationship("AgentRun", back_populates="sources")
    blog = relationship("Blog", back_populates="sources")
    claims = relationship("Claim", back_populates="source")

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet or "",
            "domain": self.domain or "",
            "reliability_score": self.reliability_score,
        }


class FactCheck(Base):
    __tablename__ = "fact_checks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    score = Column(Float, nullable=False, default=8.5)
    passed = Column(Boolean, nullable=False, default=True)
    critique = Column(Text, nullable=True)
    hallucinations_json = Column(Text, default="[]")
    unverified_commands_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run = relationship("AgentRun", back_populates="fact_checks")
    blog_version = relationship("BlogVersion", back_populates="fact_checks")
    claims = relationship("Claim", back_populates="fact_check", cascade="all, delete-orphan")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    fact_check_id = Column(Integer, ForeignKey("fact_checks.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="verified")  # verified, unverified, disputed
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    fact_check = relationship("FactCheck", back_populates="claims")
    source = relationship("SourceDocument", back_populates="claims")


# ==========================================
# 5. Prompts & Product Analytics
# ==========================================
class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    prompt_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    template_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReaderEvent(Base):
    __tablename__ = "reader_events"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # view, scroll, copy, download_pdf, download_md, share
    metadata_json = Column(Text, default="{}")
    ip_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    blog = relationship("Blog", back_populates="reader_events")
