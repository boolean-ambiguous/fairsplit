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
    def make(names: list[str], group_name: str = "Trip") -> int:
        resp = client.post("/groups", data={"name": group_name})
        assert resp.status_code == 200
        group_id = 1
        for name in names:
            resp = client.post(f"/groups/{group_id}/members", data={"name": name})
            assert resp.status_code == 200
        return group_id

    return make
