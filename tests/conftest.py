import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.database as database
from app.main import app
from app.models import Group, Member


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
def group_with_members(client, engine):
    def make(names: list[str], group_name: str = "Trip"):
        resp = client.post("/groups", data={"name": group_name})
        assert resp.status_code == 200
        with Session(engine) as session:
            group_id = session.exec(
                select(Group.id).where(Group.name == group_name)
            ).one()
            for name in names:
                resp = client.post(
                    f"/groups/{group_id}/members", data={"name": name}
                )
                assert resp.status_code == 200
        return group_id

    return make


@pytest.fixture
def member_ids(engine):
    """Look up a group's member ids by name, in insertion order."""

    def get(group_id, names: list[str]):
        with Session(engine) as session:
            members = {
                m.name: m.id
                for m in session.exec(
                    select(Member).where(Member.group_id == group_id)
                ).all()
            }
        return [members[name] for name in names]

    return get
