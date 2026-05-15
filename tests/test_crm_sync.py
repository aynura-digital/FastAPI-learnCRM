"""Tests for CRM → Academic synchronization endpoints."""

STUDENT_PAYLOAD = {
    "crm_student_id": "CRM-STU-10045",
    "first_name": "Aisha",
    "last_name": "Karimova",
    "email": "aisha@example.com",
    "phone": "+998901234567",
    "date_of_birth": "2005-03-15",
    "enrollment_date": "2025-09-01",
    "course_name": "Python Backend Development",
    "group_id": "GRP-2025-PY-03",
}


def test_sync_student_creates_new(client):
    resp = client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["crm_student_id"] == "CRM-STU-10045"
    assert data["first_name"] == "Aisha"
    assert data["is_active"] is True


def test_sync_student_updates_existing(client):
    first = client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)
    assert first.status_code == 201

    updated = {**STUDENT_PAYLOAD, "first_name": "Aysha"}
    resp = client.post("/api/v1/crm/students/sync", json=updated)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Aysha"


def test_get_student(client):
    client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)
    resp = client.get("/api/v1/crm/students/CRM-STU-10045")
    assert resp.status_code == 200
    assert resp.json()["email"] == "aisha@example.com"


def test_get_student_not_found(client):
    resp = client.get("/api/v1/crm/students/NONEXISTENT")
    assert resp.status_code == 404


def test_list_students(client):
    client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)
    resp = client.get("/api/v1/crm/students")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_patch_student(client):
    client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)
    resp = client.patch(
        "/api/v1/crm/students/CRM-STU-10045",
        json={"course_name": "Full-Stack Development"},
    )
    assert resp.status_code == 200
    assert resp.json()["course_name"] == "Full-Stack Development"


def test_sync_payment(client):
    # First create the student
    client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)

    payment = {
        "crm_payment_id": "PAY-20250901-001",
        "crm_student_id": "CRM-STU-10045",
        "amount": 350.00,
        "currency": "USD",
        "payment_status": "Paid",
        "payment_date": "2025-09-01",
        "invoice_number": "INV-10045",
        "modules_to_unlock": ["MOD-PY-101", "MOD-PY-102"],
    }
    resp = client.post("/api/v1/crm/payments/sync", json=payment)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Paid"
    assert len(data["modules_unlocked"]) == 2


def test_sync_payment_student_not_found(client):
    payment = {
        "crm_payment_id": "PAY-GHOST-001",
        "crm_student_id": "NONEXISTENT",
        "amount": 100.0,
        "currency": "USD",
        "payment_status": "Paid",
    }
    resp = client.post("/api/v1/crm/payments/sync", json=payment)
    assert resp.status_code == 404


def test_invalid_phone_rejected(client):
    bad = {**STUDENT_PAYLOAD, "phone": "not-a-phone"}
    resp = client.post("/api/v1/crm/students/sync", json=bad)
    assert resp.status_code == 422


def test_invalid_email_rejected(client):
    bad = {**STUDENT_PAYLOAD, "email": "not-an-email"}
    resp = client.post("/api/v1/crm/students/sync", json=bad)
    assert resp.status_code == 422
