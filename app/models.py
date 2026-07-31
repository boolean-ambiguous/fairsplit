from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utcnow)


class Member(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    name: str


class Expense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="group.id", index=True)
    description: str
    amount_cents: int
    payer_id: int = Field(foreign_key="member.id")
    created_at: datetime = Field(default_factory=utcnow)


class ExpenseShare(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_id: int = Field(foreign_key="expense.id", index=True)
    member_id: int = Field(foreign_key="member.id", index=True)
    share_cents: int
