import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.database import db

@pytest.fixture(autouse=True)
def reset_database():
    """Reset the in-memory database to seed state before each test for clean isolation."""
    db.reset()
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def counselor_auth_headers(client):
    """Obtain valid JWT headers for primary counsellor (Dr. Elena Rostova)."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "counselor.disha@institution.edu",
        "password": "DishaCounsellor@2026"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    campus_id = resp.json()["campus_id"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": campus_id
    }

@pytest.fixture
def other_counselor_auth_headers(client):
    """Obtain valid JWT headers for secondary counsellor (Dr. Marcus Vance)."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "counselor.other@institution.edu",
        "password": "OtherCounsellor@2026"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    campus_id = resp.json()["campus_id"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": campus_id
    }

@pytest.fixture
def faculty_auth_headers(client):
    """Obtain valid JWT headers for faculty user (Prof. Johnathan Myers)."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "faculty.john@institution.edu",
        "password": "FacultyPass@2026"
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    campus_id = resp.json()["campus_id"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": campus_id
    }

