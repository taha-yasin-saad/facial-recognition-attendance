import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app
from app.db import Base, engine, SessionLocal
from app.utils.security import get_password_hash
from app import models

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # use sqlite memory for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    admin = models.Admin(username="test", hashed_password=get_password_hash("secret"))
    db.add(admin)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def test_login_success():
    resp = client.post("/auth/login", json={"username": "test", "password": "secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


def test_login_fail():
    resp = client.post("/auth/login", json={"username": "test", "password": "wrong"})
    assert resp.status_code == 401


def test_enroll_validation():
    # create employee
    # login to get token
    login = client.post("/auth/login", json={"username": "test", "password": "secret"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/employees", json={"employee_code": "E1", "full_name": "Foo"}, headers=headers)
    assert resp.status_code == 200
    emp = resp.json()
    emp_id = emp["id"]
    # upload non-face images should fail
    with open(__file__, "rb") as f:
        resp2 = client.post(f"/employees/{emp_id}/enroll", files={"files": ("test.py", f, "image/jpeg")} , headers=headers)
    assert resp2.status_code == 400


def test_challenge_and_liveness_and_recognition():
    # get challenge
    resp = client.get("/kiosk/challenge", headers={"device-id": "dev1"})
    assert resp.status_code == 200
    ch = resp.json()
    assert "challenge_id" in ch
    # liveness with no frames -> fail
    resp2 = client.post("/kiosk/liveness", headers={"challenge-id": ch["challenge_id"], "device-id":"dev1"}, files={})
    assert resp2.status_code == 422 or resp2.status_code == 400

    # now try with a invalid frame list
    badfile = ("files", ("foo.jpg", BytesIO(b"notjpg"), "image/jpeg"))
    resp3 = client.post(
        "/kiosk/liveness",
        headers={"challenge-id": ch["challenge_id"], "device-id": "dev1"},
        files=[badfile],
    )
    assert resp3.status_code == 200
    assert "passed" in resp3.json()

    # recognition without a valid embedding should 400
    resp4 = client.post(
        "/kiosk/recognize",
        headers={"type": "IN", "device-id": "dev1"},
        files=[badfile],
    )
    assert resp4.status_code == 400

