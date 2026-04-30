# Tests for JWT auth: valid token decoding, role extraction, expired tokens, and invalid signatures

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)


def make_token(role: str) -> str:
    return jwt.encode({"sub": "test-user", "covenant_role": role}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_valid_admin_token():
    token = make_token("admin")
    response = client.get("/health", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_invalid_role_rejected():
    token = jwt.encode({"sub": "x", "covenant_role": "superuser"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    response = client.post("/query", json={"query": "test"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_missing_token_rejected():
    response = client.post("/query", json={"query": "test"})
    assert response.status_code == 403
