import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Agentic AI Document Intelligence & Compliance Checker"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # In production set CORS_ORIGINS to your Vercel URL(s), e.g.
    # CORS_ORIGINS=["https://your-app.vercel.app"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    # Regex that is also allowed (lets Vercel preview deployments through).
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"

    # LLM Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5-5"

    DEFAULT_LLM_PROVIDER: str = "mock"  # "gemini", "openai", "anthropic", "mock"

    # ---- Relational storage (PostgreSQL in production, SQLite for zero-config dev)
    DATABASE_URL: str = "sqlite+aiosqlite:///./compliance_checker.db"

    # ---- Redis (agent memory, event log, cached state)
    REDIS_URL: str = "redis://localhost:6379/0"
    # When true no Redis connection is attempted and state lives in process memory.
    USE_IN_MEMORY_REDIS: bool = True
    REDIS_TTL_SECONDS: int = 60 * 60 * 24

    # ---- Embeddings + vector database (RAG)
    # "sentence-transformers" -> dense embeddings; "none" -> lexical retrieval only
    EMBEDDING_BACKEND: str = "sentence-transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # "chroma" | "faiss" | "memory"
    VECTOR_BACKEND: str = "chroma"
    # Empty string -> ephemeral (in-process) Chroma; a path -> persistent Chroma
    CHROMA_PERSIST_DIR: str = ""

    # ---- Uploads
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./generated_reports"
    MAX_UPLOAD_MB: int = 25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
