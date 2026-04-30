# RAG query pipeline: OPA policy check → pgvector similarity search → Claude Sonnet generation

from fastapi import APIRouter, Depends

from app.auth import decode_token
from app.claude_client import generate
from app.opa_client import enforce

router = APIRouter(prefix="/query", tags=["query"])


@router.post("")
async def query(body: dict, token: dict = Depends(decode_token)) -> dict:
    role = token["covenant_role"]
    classification = body.get("classification", "internal")
    user_query = body["query"]

    # OPA enforces access — if denied, raises 403 before any retrieval
    await enforce(role=role, action="query", classification=classification)

    # TODO: embed user_query, run pgvector similarity search filtered by classification
    chunks: list[str] = []

    answer = await generate(query=user_query, chunks=chunks)
    return {"answer": answer, "role": role}
