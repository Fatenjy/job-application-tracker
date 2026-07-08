"""Shared pytest fixtures.

Key principle: tests run against a dedicated jobtracker_test database,
created on the fly — NEVER against the real data.
"""

import os

# Must happen before any app import: Settings reads env vars at import time,
# and environment variables take precedence over the .env file.
os.environ["POSTGRES_DB"] = "jobtracker_test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app

test_engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def _ensure_test_database() -> None:
    """Create jobtracker_test if it does not exist yet (CREATE DATABASE
    cannot run inside a transaction, hence isolation_level autocommit)."""
    admin_url = settings.database_url.replace(f"/{settings.postgres_db}", "/jobtracker")
    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.postgres_db},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{settings.postgres_db}"'))
        admin_engine.dispose()
    except Exception:
        # In CI the service may already be the test database itself.
        pass


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    _ensure_test_database()
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Every test starts from an empty, predictable state."""
    yield
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE applications, jobs, users RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """API test client whose requests hit the test database."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # Plain TestClient (no context manager): the lifespan does not run, so
    # the scheduler stays off during tests.
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register(client: TestClient, email: str, password: str = "password123") -> str:
    """Register a user and return an Authorization header value."""
    res = client.post("/auth/register", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    return f"Bearer {res.json()['access_token']}"


@pytest.fixture()
def auth(client):
    """A registered user's bearer token header: {'Authorization': 'Bearer ...'}."""
    return {"Authorization": _register(client, "user@test.com")}


@pytest.fixture()
def other_auth(client):
    """A second, different user — for per-user isolation tests."""
    return {"Authorization": _register(client, "other@test.com")}
