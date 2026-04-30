import uuid
from typing import Literal

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import decode_token
from app.opa_client import enforce

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = structlog.get_logger()

CHUNK_SIZE = 500
Classification = Literal["public", "internal", "confidential"]


class IngestRequest(BaseModel):
    content: str
    classification: Classification = "internal"


def _chunk(body: str) -> list[str]:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    for para in paragraphs:
        if len(buf) + len(para) > CHUNK_SIZE and buf:
            chunks.append(buf.strip())
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf.strip())
    return chunks or [body]


def _vec_str(embedding: list[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


@router.post("")
async def ingest(
    body: IngestRequest, request: Request, token: dict = Depends(decode_token)
) -> dict:
    role = token["covenant_role"]
    await enforce(role=role, action="ingest", classification=body.classification)

    chunks = _chunk(body.content)
    embedder = request.app.state.embedder
    vectors = embedder.encode(chunks).tolist()

    doc_ids = []
    async with request.app.state.engine.begin() as conn:
        for chunk, vec in zip(chunks, vectors):
            doc_id = str(uuid.uuid4())
            await conn.execute(
                text(
                    "INSERT INTO documents (id, content, embedding, classification) "
                    "VALUES (:id, :content, CAST(:emb AS vector), :cls)"
                ),
                {"id": doc_id, "content": chunk, "emb": _vec_str(vec), "cls": body.classification},
            )
            doc_ids.append(doc_id)

    logger.info("documents_ingested", count=len(chunks), classification=body.classification)
    return {"status": "accepted", "chunks": len(chunks), "doc_ids": doc_ids}
