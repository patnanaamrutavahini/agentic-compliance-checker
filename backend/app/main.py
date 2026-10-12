from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.config import settings
from app.core.database import init_db, database_dialect
from app.core.memory import memory_store
from app.ingestion.embeddings import get_embedder
from app.api.routes_documents import router as doc_router
from app.api.routes_compliance import router as compliance_router
from app.api.routes_samples import router as samples_router
from app.api.routes_export import router as export_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("compliance_checker")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database and Agent Memory...")
    await init_db()
    # Load the embedding model in the background so the first audit is not slowed down.
    warmup = asyncio.create_task(asyncio.to_thread(lambda: get_embedder().available))
    logger.info("System Ready to Process Compliance Audits.")
    yield
    warmup.cancel()
    logger.info("Shutting down Compliance Checker.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic AI Document Intelligence & Compliance Checker API with 6 Specialized Agents and Strict Grounding",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(compliance_router)
app.include_router(doc_router)
app.include_router(samples_router)
app.include_router(export_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "agents": [
            "Document Classification Agent",
            "Information Extraction Agent",
            "Requirement Extraction Agent",
            "Compliance Agent",
            "Discrepancy Agent",
            "Decision / Reviewer Agent"
        ],
        "endpoints": {
            "docs": "/docs",
            "compliance_analyze": "/api/compliance/analyze",
            "sample_scenarios": "/api/samples",
            "document_upload": "/api/documents/upload"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Agentic AI Compliance Checker",
        "components": {
            "database": database_dialect(),
            "agent_memory": await memory_store.backend_name(),
            "vector_backend": settings.VECTOR_BACKEND,
            "embedding_model": settings.EMBEDDING_MODEL if settings.EMBEDDING_BACKEND != "none" else "disabled (lexical only)",
            "llm_provider_default": settings.DEFAULT_LLM_PROVIDER,
        },
    }
