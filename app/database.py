import os

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn
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


def _sync_schema() -> None:
    """Add columns/indexes that newer models introduced to tables that
    already exist in the database — create_all() only creates tables that
    are missing entirely, it never alters an existing table, so a column
    added to a model here doesn't show up on a database created by an
    earlier deploy."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                # Always add as nullable, even if the model marks it
                # required — existing rows have no value for it yet.
                original_nullable = column.nullable
                column.nullable = True
                try:
                    ddl = CreateColumn(column).compile(dialect=engine.dialect)
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
                finally:
                    column.nullable = original_nullable
            for index in table.indexes:
                index.create(conn, checkfirst=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _sync_schema()


def get_session():
    with Session(engine) as session:
        yield session
