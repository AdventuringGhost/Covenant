# Tests for the RAG query pipeline: OPA allow/deny enforcement, role-filtered results, auditor lockout

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings
from app.main import app

client = TestClient(app)


def make_token(role: str) -> str:
    return jwt.encode({"sub": "u1", "covenant_role": role}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@patch("app.opa_client.enforce", new_callable=AsyncMock)
@patch("app.claude_client.generate", new_callable=AsyncMock, return_value="answer")
def test_user_query_allowed(mock_gen, mock_enforce):
    token = make_token("user")
    response = client.post("/query", json={"query": "what is X?", "classification": "internal"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["answer"] == "answer"


@patch("app.opa_client.enforce", new_callable=AsyncMock, side_effect=Exception("Access denied by policy"))
def test_auditor_query_blocked(mock_enforce):
    token = make_token("auditor")
    response = client.post("/query", json={"query": "what is X?", "classification": "internal"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code != 200
