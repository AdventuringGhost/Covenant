# FastAPI entry point: registers ingest, query, and audit routers; wires up lifespan and middleware

from fastapi import FastAPI

from app.ingest import router as ingest_router
from app.query import router as query_router

app = FastAPI(title="Covenant", description="Secure RAG pipeline with OPA-enforced RBAC")

app.include_router(ingest_router)
app.include_router(query_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
