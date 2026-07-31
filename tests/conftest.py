import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.database as database
from app.main import app


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
    with TestClient(app) as client:
        yield client


@pytest.fixture
def group_with_members(client):
    def make(names: list[str], group_name: str = "Trip"):
        resp = client.post("/api/groups", json={"name": group_name})
        assert resp.status_code == 201
        group_id = uuid.UUID(resp.json()["id"])
        member_ids = {}
        for name in names:
            resp = client.post(
                f"/api/groups/{group_id}/members", json={"name": name}
            )
            assert resp.status_code == 200
            for m in resp.json()["members"]:
                member_ids[m["name"]] = uuid.UUID(m["id"])
        make.member_ids = member_ids
        return group_id

    return make


@pytest.fixture
def member_ids(group_with_members):
    """Return the last-created group's member ids by name, in insertion order."""

    def get(group_id, names: list[str]):
        return [group_with_members.member_ids[name] for name in names]

    return get
