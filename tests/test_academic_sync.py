"""Tests for Academic System → CRM synchronization endpoints."""

STUDENT_PAYLOAD = {
    "crm_student_id": "CRM-STU-10045",
    "first_name": "Aisha",
    "last_name": "Karimova",
    "email": "aisha@example.com",
}

ACADEMIC_RECORD = {
    "crm_student_id": "CRM-STU-10045",
    "course_code": "PY-BACKEND-2025",
    "module_name": "Django REST Framework",
    "attendance_pct": 92.5,
    "grade": "A",
    "score": 95.0,
    "total_classes": 24,
    "attended_classes": 22,
    "status": "in_progress",
    "instructor_notes": "Excellent participation",
}


def _seed_student(client):
    client.post("/api/v1/crm/students/sync", json=STUDENT_PAYLOAD)


def test_create_academic_record(client):
    _seed_student(client)
    resp = client.post("/api/v1/academic/records", json=ACADEMIC_RECORD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["course_code"] == "PY-BACKEND-2025"
    assert data["attendance_pct"] == 92.5


def test_create_record_student_not_found(client):
    resp = client.post("/api/v1/academic/records", json=ACADEMIC_RECORD)
    assert resp.status_code == 404


def test_get_student_records(client):
    _seed_student(client)
    client.post("/api/v1/academic/records", json=ACADEMIC_RECORD)
    resp = client.get("/api/v1/academic/records/CRM-STU-10045")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_academic_record(client):
    _seed_student(client)
    create_resp = client.post("/api/v1/academic/records", json=ACADEMIC_RECORD)
    record_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/academic/records/{record_id}",
        json={"grade": "A+", "score": 98.0, "status": "completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["grade"] == "A+"
    assert resp.json()["status"] == "completed"


def test_crm_payload(client):
    _seed_student(client)
    client.post("/api/v1/academic/records", json=ACADEMIC_RECORD)
    resp = client.get("/api/v1/academic/progress/CRM-STU-10045/crm-payload")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["crm_student_id"] == "CRM-STU-10045"
    assert data[0]["student_name"] == "Aisha Karimova"


def test_attendance_out_of_range_rejected(client):
    _seed_student(client)
    bad = {**ACADEMIC_RECORD, "attendance_pct": 150.0}
    resp = client.post("/api/v1/academic/records", json=bad)
    assert resp.status_code == 422
