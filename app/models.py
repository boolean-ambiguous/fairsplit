import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Group(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utcnow)


class Member(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="group.id", index=True)
    name: str
    created_at: datetime = Field(default_factory=utcnow)


class Expense(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="group.id", index=True)
    description: str
    amount_cents: int
    payer_id: uuid.UUID = Field(foreign_key="member.id")
    created_at: datetime = Field(default_factory=utcnow)


class ExpenseShare(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    expense_id: uuid.UUID = Field(foreign_key="expense.id", index=True)
    member_id: uuid.UUID = Field(foreign_key="member.id", index=True)
    share_cents: int
