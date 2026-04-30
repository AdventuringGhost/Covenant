import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.ingest import router as ingest_router
from app.query import router as query_router

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
)
logger = structlog.get_logger()

_DDL = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    """
    CREATE TABLE IF NOT EXISTS documents (
        id             TEXT PRIMARY KEY,
        content        TEXT NOT NULL,
        embedding      vector(384) NOT NULL,
        classification TEXT NOT NULL,
        created_at     TIMESTAMPTZ DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id             BIGSERIAL PRIMARY KEY,
        role           TEXT NOT NULL,
        action         TEXT NOT NULL,
        classification TEXT,
        allowed        BOOLEAN NOT NULL,
        created_at     TIMESTAMPTZ DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS docs_emb_idx ON documents USING ivfflat (embedding vector_cosine_ops)",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        for ddl in _DDL:
            await conn.execute(text(ddl))
    app.state.engine = engine
    app.state.embedder = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("startup_complete")
    yield
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title="Covenant",
    description="Secure RAG pipeline with OPA-enforced RBAC",
    lifespan=lifespan,
)
app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
