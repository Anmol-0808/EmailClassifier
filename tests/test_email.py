import os
os.environ["ENV"] = "test"

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_email_authorized():
    email = f"auth_{uuid.uuid4()}@gmail.com"

    response = client.post(
        "/emails",
        headers={"X-API-Key": "08anmol08"},
        json={
            "email": email,
            "email_type": "newsletter"
        }
    )

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert "id" in response.json()


def test_duplicate_email():
    email = f"dup_{uuid.uuid4()}@gmail.com"

    # First create → should succeed
    first = client.post(
        "/emails",
        headers={"X-API-Key": "08anmol08"},
        json={
            "email": email,
            "email_type": "newsletter"
        }
    )
    assert first.status_code == 201

    # Second create → should fail
    second = client.post(
        "/emails",
        headers={"X-API-Key": "08anmol08"},
        json={
            "email": email,
            "email_type": "newsletter"
        }
    )

    assert second.status_code == 400


def test_update_email_unauthorized():
    response = client.patch(
        "/emails/1",
        json={"email_type": "support"}
    )

    assert response.status_code == 401


def test_delete_email():
    email = f"delete_{uuid.uuid4()}@gmail.com"

    create = client.post(
        "/emails",
        headers={"X-API-Key": "08anmol08"},
        json={
            "email": email,
            "email_type": "newsletter"
        }
    )

    assert create.status_code == 201
    email_id = create.json()["id"]

    delete = client.delete(
        f"/emails/{email_id}",
        headers={"X-API-Key": "08anmol08"}
    )

    assert delete.status_code == 204
