import httpx
import structlog
from fastapi import HTTPException, status

from app.config import settings

logger = structlog.get_logger()

_OPA_URL = f"{settings.opa_url}/v1/data/covenant/authz/allow"


async def enforce(role: str, action: str, classification: str) -> None:
    """POST to OPA and raise 403 if the policy denies access."""
    payload = {"input": {"role": role, "action": action, "classification": classification}}
    async with httpx.AsyncClient() as client:
        response = await client.post(_OPA_URL, json=payload, timeout=5.0)
    response.raise_for_status()
    allowed = response.json().get("result", False)
    logger.info("opa_decision", role=role, action=action, classification=classification, allowed=allowed)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied by policy")
