import uuid
from datetime import datetime

from pydantic import BaseModel


class GroupOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class MemberOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime


class ExpenseOut(BaseModel):
    id: uuid.UUID
    description: str
    amount_cents: int
    payer_id: uuid.UUID
    created_at: datetime


class BalanceOut(BaseModel):
    member_id: uuid.UUID
    balance_cents: int


class SettlementOut(BaseModel):
    from_member: uuid.UUID
    to_member: uuid.UUID
    amount_cents: int


class GroupDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    members: list[MemberOut]
    expenses: list[ExpenseOut]
    balances: list[BalanceOut]
    settlements: list[SettlementOut]


class GroupCreate(BaseModel):
    name: str


class MemberCreate(BaseModel):
    name: str


class ExpenseCreate(BaseModel):
    description: str
    amount: str
    payer_id: uuid.UUID
    participant_ids: list[uuid.UUID]
    split_mode: str = "even"
    exact_shares: dict[uuid.UUID, str] | None = None
