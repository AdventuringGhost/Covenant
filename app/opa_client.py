# OPA client: POST input to OPA REST API and enforce the allow decision before any data retrieval

import httpx
from fastapi import HTTPException, status

from app.config import settings

OPA_QUERY_URL = f"{settings.opa_url}/v1/data/covenant/authz/allow"


async def enforce(role: str, action: str, classification: str) -> None:
    """Raise 403 if OPA denies the request."""
    input_doc = {"input": {"role": role, "action": action, "classification": classification}}
    async with httpx.AsyncClient() as client:
        response = await client.post(OPA_QUERY_URL, json=input_doc, timeout=5.0)
    response.raise_for_status()
    allowed = response.json().get("result", False)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied by policy")
