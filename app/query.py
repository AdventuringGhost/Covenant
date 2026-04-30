import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import bindparam, text

from app.auth import decode_token
from app.claude_client import generate
from app.opa_client import enforce

router = APIRouter(prefix="/query", tags=["query"])
logger = structlog.get_logger()

TOP_K = 5

_ROLE_ALLOWED: dict[str, list[str]] = {
    "admin": ["public", "internal", "confidential"],
    "user": ["public", "internal"],
    "auditor": [],
}


class QueryRequest(BaseModel):
    query: str
    classification: str = "internal"


def _vec_str(embedding: list[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


@router.post("")
async def query(
    body: QueryRequest, request: Request, token: dict = Depends(decode_token)
) -> dict:
    role = token["covenant_role"]
    await enforce(role=role, action="query", classification=body.classification)

    # Auditors see audit logs only — never document content
    if role == "auditor":
        async with request.app.state.engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT role, action, classification, allowed, created_at "
                    "FROM audit_logs ORDER BY created_at DESC LIMIT 50"
                )
            )
            logs = [dict(r._mapping) for r in rows.fetchall()]
        return {"audit_logs": logs}

    embedder = request.app.state.embedder
    q_vec_str = _vec_str(embedder.encode([body.query])[0].tolist())
    allowed = _ROLE_ALLOWED.get(role, ["public"])

    stmt = text(
        "SELECT content FROM documents "
        "WHERE classification IN :cls "
        "ORDER BY embedding <=> CAST(:q AS vector) "
        "LIMIT :k"
    ).bindparams(bindparam("cls", expanding=True))

    async with request.app.state.engine.connect() as conn:
        rows = await conn.execute(stmt, {"cls": allowed, "q": q_vec_str, "k": TOP_K})
        chunks = [r[0] for r in rows.fetchall()]

    answer = await generate(query=body.query, chunks=chunks, role=role)
    logger.info("query_served", role=role, chunks_found=len(chunks))
    return {"answer": answer, "role": role, "sources": len(chunks)}
