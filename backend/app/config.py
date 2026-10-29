import os
from pathlib import Path
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve absolute path to project root .env
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"
BACKEND_ENV_PATH = ROOT_DIR / "backend" / ".env"

# Ensure repository .env always overrides any stale Windows system environment variables
from dotenv import load_dotenv
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
if BACKEND_ENV_PATH.exists():
    load_dotenv(BACKEND_ENV_PATH, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(ENV_PATH), str(BACKEND_ENV_PATH), ".env", "../.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General LLM Settings
    MODEL_PROVIDER: str = "groq"
    MODEL_NAME: str = "openai/gpt-oss-20b"
    MODEL_TEMPERATURE: float = 0.7

    # API Keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Verifier & Fallback Settings
    VERIFIER_MODEL: Optional[str] = None
    REVIEW_FALLBACK: str = "flag"  # "fail" | "flag"

    # Research & Search Controls
    MIN_SOURCES_REQUIRED: int = 2
    MIN_FACTS_REQUIRED: int = 2
    SEARCH_TIMEOUT_SECONDS: float = 10.0
    SEARCH_CACHE_TTL_HOURS: int = 24
    GROQ_CONCURRENCY_LIMIT: int = 4

    # PostgreSQL Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "root"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "blog_db"
    DATABASE_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Observability (LangSmith)
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "autonomous-blog-engine"

    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    
    # Configure LangSmith environment if enabled
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

    return settings
