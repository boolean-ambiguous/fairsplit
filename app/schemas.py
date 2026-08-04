import uuid
from datetime import date, datetime

from pydantic import BaseModel

CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]


# ---- Auth ----


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    theme: str


class SignupRequest(BaseModel):
    email: str


class VerifyRequest(BaseModel):
    token: str


class NameRequest(BaseModel):
    name: str


class UpdateMeRequest(BaseModel):
    name: str | None = None
    theme: str | None = None


# ---- Groups / members ----


class MemberOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str | None
    user_id: uuid.UUID | None
    created_at: datetime


class InviteMember(BaseModel):
    name: str
    email: str | None = None


class GroupCreate(BaseModel):
    name: str
    currency: str = "USD"
    photo_data_url: str | None = None
    invites: list[InviteMember] = []


class GroupUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    photo_data_url: str | None = None


class MemberCreate(BaseModel):
    name: str
    email: str | None = None


class MemberUpdate(BaseModel):
    name: str


class GroupOut(BaseModel):
    id: uuid.UUID
    name: str
    currency: str
    photo_data_url: str | None
    created_at: datetime
    member_count: int
    balance_cents: int


# ---- Expenses ----


class ExpenseHistoryChange(BaseModel):
    field: str
    previous: str
    updated: str


class ExpenseHistoryEntryOut(BaseModel):
    changed_by: uuid.UUID
    changed_at: datetime
    changes: list[ExpenseHistoryChange]


class ExpenseOut(BaseModel):
    id: uuid.UUID
    description: str
    amount_cents: int
    payer_id: uuid.UUID
    date: date
    notes: str | None
    receipt_data_url: str | None
    split_mode: str
    participant_ids: list[uuid.UUID]
    shares: dict[uuid.UUID, int]
    created_by: uuid.UUID
    created_at: datetime
    updated_by: uuid.UUID | None
    updated_at: datetime | None
    can_delete: bool
    history: list[ExpenseHistoryEntryOut]


class ExpenseCreate(BaseModel):
    description: str
    amount: str
    date: date
    payer_id: uuid.UUID
    participant_ids: list[uuid.UUID]
    split_mode: str = "even"
    exact_shares: dict[uuid.UUID, str] | None = None
    notes: str | None = None
    receipt_data_url: str | None = None


class ExpenseUpdate(ExpenseCreate):
    pass


# ---- Balances / settlements ----


class BalanceOut(BaseModel):
    member_id: uuid.UUID
    balance_cents: int


class SuggestedPaymentOut(BaseModel):
    from_member: uuid.UUID
    to_member: uuid.UUID
    amount_cents: int


class SettlementRecordOut(BaseModel):
    id: uuid.UUID
    from_member: uuid.UUID
    to_member: uuid.UUID
    amount_cents: int
    recorded_by: uuid.UUID
    settled_at: datetime


class SettlementCreate(BaseModel):
    from_member: uuid.UUID
    to_member: uuid.UUID
    amount: str


class GroupDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    currency: str
    photo_data_url: str | None
    created_at: datetime
    members: list[MemberOut]
    expenses: list[ExpenseOut]
    balances: list[BalanceOut]
    my_positions: list[BalanceOut]
    suggested_settlements: list[SuggestedPaymentOut]
    settlement_history: list[SettlementRecordOut]


# ---- Dashboard ----


class DashboardGroupOut(BaseModel):
    id: uuid.UUID
    name: str
    currency: str
    photo_data_url: str | None
    last_expense_at: datetime | None
    balance_cents: int


class FlowPointOut(BaseModel):
    date: date
    owed_cents: int
    owe_cents: int


class OpenPositionOut(BaseModel):
    group_id: uuid.UUID
    group_name: str
    currency: str
    other_name: str
    net_cents: int


class DashboardOut(BaseModel):
    name: str
    groups: list[DashboardGroupOut]
    flow: list[FlowPointOut]
    open_positions: list[OpenPositionOut]
