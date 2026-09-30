"""Integration tests use a separate PostgreSQL schema and real migrations."""
import os
import uuid
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient
from app.db import engine
from app.main import app
from app.seed import seed
from app.config import settings


@pytest.fixture(scope="session", autouse=True)
def schema():
    name = "test_" + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{name}"'))
    # Every pooled connection is restricted to this test schema.
    from sqlalchemy import event
    def set_schema(dbapi_connection, connection_record):
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{name}", public')
        dbapi_connection.commit()
    engine.dispose()
    event.listen(engine, "connect", set_schema)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    command.upgrade(cfg, "head")
    with engine.connect() as connection:
        actual = connection.scalar(text("SELECT table_schema FROM information_schema.tables WHERE table_name='nodes' AND table_schema=:name"), {"name": name})
        assert actual == name, "Tests must never use the public application schema"
    seed()
    yield
    engine.dispose()
    event.remove(engine, "connect", set_schema)
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{name}" CASCADE'))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin(client):
    r = client.post("/api/auth/login", json={"email": "admin@nexarena.local", "password": settings.demo_password})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def staff(client):
    r = client.post("/api/auth/login", json={"email": "staff@nexarena.local", "password": settings.demo_password})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture
def enrolled(client, admin):
    branch = client.get("/api/branches", headers=admin).json()[0]
    body = {"machine_id": "integration-" + uuid.uuid4().hex, "hostname": "TEST-PC", "name": "Test station", "branch_id": branch["id"], "os": "Windows test fixture", "agent_secret": uuid.uuid4().hex}
    r = client.post("/api/nodes/register", json=body, headers={"X-Agent-Key": settings.agent_enrollment_key})
    assert r.status_code == 200
    return r.json()["node_id"], body["agent_secret"]
