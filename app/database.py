import os

from sqlmodel import Session, SQLModel, create_engine


def _normalize_database_url(url: str) -> str:
    """Accept a plain postgres/postgresql URL (e.g. pasted straight from
    Supabase's connection string) and route it through psycopg (v3), the
    driver this project installs — SQLAlchemy doesn't infer a driver from a
    bare `postgresql://` scheme on its own."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = _normalize_database_url(os.environ.get("FAIRSPLIT_DB", "sqlite:///fairsplit.db"))

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
