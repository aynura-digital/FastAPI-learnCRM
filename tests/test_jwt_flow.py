"""End-to-end JWT auth test.

Most tests in this suite override ``get_current_user`` to keep them focused
on business logic. This file deliberately removes that override for the
duration of the test so we exercise the real token-issue / token-consume
path through the live FastAPI dependency.
"""

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app


@pytest.fixture
def jwt_client():
    saved = app.dependency_overrides.pop(get_current_user, None)
    try:
        yield TestClient(app)
    finally:
        if saved is not None:
            app.dependency_overrides[get_current_user] = saved


def test_protected_endpoint_requires_token(jwt_client):
    resp = jwt_client.get("/api/v1/crm/students")
    assert resp.status_code in (401, 403)


def test_full_token_issue_and_use(jwt_client):
    register = jwt_client.post(
        "/auth/register",
        json={
            "username": "jwt_user",
            "password": "S3cure!pass",
            "service_name": "JWT Test",
        },
        headers={"X-API-Key": "test-api-key"},
    )
    assert register.status_code == 201

    token_resp = jwt_client.post(
        "/auth/token",
        json={"username": "jwt_user", "password": "S3cure!pass"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    assert token

    authed = jwt_client.get(
        "/api/v1/crm/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert authed.status_code == 200
    assert isinstance(authed.json(), list)

    bogus = jwt_client.get(
        "/api/v1/crm/students",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert bogus.status_code == 401
