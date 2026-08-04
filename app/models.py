import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str | None = None
    theme: str = Field(default="dark")
    created_at: datetime = Field(default_factory=utcnow)


class MagicLinkToken(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    consumed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class LoginSession(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)


class Group(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    currency: str = Field(default="USD")
    photo_data_url: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Member(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="group.id", index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    name: str
    email: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Expense(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="group.id", index=True)
    description: str
    amount_cents: int
    payer_id: uuid.UUID = Field(foreign_key="member.id")
    split_mode: str = Field(default="even")
    date: datetime
    notes: str | None = None
    receipt_data_url: str | None = None
    created_by: uuid.UUID = Field(foreign_key="member.id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_by: uuid.UUID | None = Field(default=None, foreign_key="member.id")
    updated_at: datetime | None = None


class ExpenseShare(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expense.id", index=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", index=True)
    share_cents: int


class ExpenseHistoryEntry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expense.id", index=True)
    changed_by: uuid.UUID = Field(foreign_key="member.id")
    changed_at: datetime = Field(default_factory=utcnow)
    changes_json: str


class Settlement(SQLModel, table=True):
    """A recorded ('marked as paid') payment between two members — distinct
    from the computed settlement *suggestions* in services/settlements.py.
    Recorded settlements offset balances alongside expenses."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="group.id", index=True)
    from_member: uuid.UUID = Field(foreign_key="member.id")
    to_member: uuid.UUID = Field(foreign_key="member.id")
    amount_cents: int
    recorded_by: uuid.UUID = Field(foreign_key="member.id")
    settled_at: datetime = Field(default_factory=utcnow)
