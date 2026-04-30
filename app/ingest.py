# Ingestion pipeline: chunk documents, generate embeddings, store in pgvector with classification tags

from fastapi import APIRouter, Depends

from app.auth import decode_token
from app.opa_client import enforce

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
async def ingest(body: dict, token: dict = Depends(decode_token)) -> dict:
    role = token["covenant_role"]

    # Only admins may ingest documents
    await enforce(role=role, action="ingest", classification=body.get("classification", "internal"))

    # TODO: chunk body["content"], embed via model, upsert into pgvector documents table
    return {"status": "accepted", "doc_id": None}
