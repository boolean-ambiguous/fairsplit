import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.database as database
from app.main import app
from app.models import MagicLinkToken
from app.services.rate_limit import signup_ip_limiter


@pytest.fixture(autouse=True)
def _stub_email(monkeypatch):
    """Every test goes through this — signup now sends real SMTP mail, and
    tests shouldn't depend on a mail server being reachable. Tests that care
    about what was "sent" (e.g. hostile-Host-header rejection) monkeypatch
    the same target themselves, which simply overrides this stub for that
    test."""
    monkeypatch.setattr("app.routes.auth.send_magic_link", lambda email, link: None)


@pytest.fixture(autouse=True)
def _reset_signup_ip_limiter():
    # The per-IP signup limiter (app/services/rate_limit.py) is a
    # module-level singleton so it works correctly in the single-process app
    # — but that means it's shared across every test's TestClient (which all
    # report the same client host), so it must be reset per test to avoid
    # unrelated tests tripping each other's limit.
    signup_ip_limiter._hits.clear()


@pytest.fixture
def engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(database, "engine", engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine):
    # base_url must be a loopback/private host — request.base_url feeds
    # magic-link generation (app/config.py::resolve_frontend_base_url),
    # which only trusts loopback/private-network origins. The TestClient
    # default ("http://testserver") is neither.
    with TestClient(app, base_url="http://localhost") as client:
        yield client


@pytest.fixture
def signed_in(client, engine):
    """Sign up + verify + name-step a fresh user; returns (client, name) with
    the TestClient's cookies carrying the session for subsequent requests."""

    def make(name: str, email: str | None = None):
        email = email or f"{name.lower().replace(' ', '.')}@example.com"
        resp = client.post("/api/auth/signup", json={"email": email})
        assert resp.status_code == 202, resp.text

        with Session(engine) as session:
            from app.models import User

            user = session.exec(select(User).where(User.email == email.lower())).first()
            assert user is not None
            token = session.exec(
                select(MagicLinkToken)
                .where(MagicLinkToken.user_id == user.id)
                .order_by(MagicLinkToken.created_at.desc())
            ).first()
            assert token is not None

        resp = client.post("/api/auth/verify", json={"token": token.token})
        assert resp.status_code == 200, resp.text

        resp = client.post("/api/auth/name", json={"name": name})
        assert resp.status_code == 200, resp.text
        return resp.json()

    return make


@pytest.fixture
def group_with_members(client, signed_in):
    """Signs in as the first name in the list (the group creator), then
    invites the rest as placeholder members. Returns the group id; the
    TestClient ends up authenticated as the first member."""

    def make(names: list[str], group_name: str = "Trip"):
        assert names, "group_with_members needs at least one name"
        signed_in(names[0])
        resp = client.post(
            "/api/groups",
            json={
                "name": group_name,
                "currency": "USD",
                "invites": [{"name": n} for n in names[1:]],
            },
        )
        assert resp.status_code == 201, resp.text
        group_id = uuid.UUID(resp.json()["id"])
        detail = client.get(f"/api/groups/{group_id}").json()
        make.member_ids = {m["name"]: uuid.UUID(m["id"]) for m in detail["members"]}
        return group_id

    return make


@pytest.fixture
def member_ids(group_with_members):
    """Return the last-created group's member ids by name, in insertion order."""

    def get(group_id, names: list[str]):
        return [group_with_members.member_ids[name] for name in names]

    return get
