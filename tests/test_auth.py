"""Tests for authentication endpoints."""


def test_register_and_login(client):
    resp = client.post(
        "/auth/register",
        json={
            "username": "crm_service",
            "password": "securepass123",
            "service_name": "CRM System",
        },
        headers={"X-API-Key": "test-api-key"},
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "crm_service"

    resp = client.post(
        "/auth/token",
        json={"username": "crm_service", "password": "securepass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "username": "crm_svc",
            "password": "correctpass",
            "service_name": "CRM",
        },
        headers={"X-API-Key": "test-api-key"},
    )
    resp = client.post(
        "/auth/token",
        json={"username": "crm_svc", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "operational"
