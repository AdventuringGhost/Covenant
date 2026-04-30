import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer = HTTPBearer()
logger = structlog.get_logger()

_VALID_ROLES = {"admin", "user", "auditor"}


def decode_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        role = payload.get("covenant_role")
        if role not in _VALID_ROLES:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing role")
        logger.info("token_decoded", role=role)
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
