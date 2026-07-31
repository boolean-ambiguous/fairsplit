import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Expense, Group, Member
from app.schemas import (
    BalanceOut,
    ExpenseCreate,
    ExpenseOut,
    GroupCreate,
    GroupDetailOut,
    GroupOut,
    MemberCreate,
    MemberOut,
    SettlementOut,
)
from app.services.balances import compute_balances
from app.services.expenses import ExpenseError, record_expense
from app.services.money import MoneyError, parse_amount, parse_share
from app.services.settlements import suggest_settlements

router = APIRouter(prefix="/api/groups")


def get_group_or_404(session: Session, group_id: uuid.UUID) -> Group:
    group = session.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def group_members(session: Session, group_id: uuid.UUID) -> list[Member]:
    return list(
        session.exec(
            select(Member)
            .where(Member.group_id == group_id)
            .order_by(Member.created_at)
        ).all()
    )


def group_expenses(session: Session, group_id: uuid.UUID) -> list[Expense]:
    return list(
        session.exec(
            select(Expense)
            .where(Expense.group_id == group_id)
            .order_by(Expense.created_at.desc())
        ).all()
    )


def _group_detail(session: Session, group: Group) -> GroupDetailOut:
    members = group_members(session, group.id)
    expenses = group_expenses(session, group.id)
    balances = compute_balances(session, group.id)
    settlements = suggest_settlements(balances)
    return GroupDetailOut(
        id=group.id,
        name=group.name,
        created_at=group.created_at,
        members=[MemberOut(id=m.id, name=m.name, created_at=m.created_at) for m in members],
        expenses=[
            ExpenseOut(
                id=e.id,
                description=e.description,
                amount_cents=e.amount_cents,
                payer_id=e.payer_id,
                created_at=e.created_at,
            )
            for e in expenses
        ],
        balances=[
            BalanceOut(member_id=mid, balance_cents=cents)
            for mid, cents in balances.items()
        ],
        settlements=[
            SettlementOut(
                from_member=p.from_member, to_member=p.to_member, amount_cents=p.amount_cents
            )
            for p in settlements
        ],
    )


@router.get("", response_model=list[GroupOut])
def list_groups(session: Session = Depends(get_session)):
    groups = session.exec(select(Group).order_by(Group.created_at)).all()
    return [GroupOut(id=g.id, name=g.name, created_at=g.created_at) for g in groups]


@router.post("", response_model=GroupOut, status_code=201)
def create_group(body: GroupCreate, session: Session = Depends(get_session)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Group name is required")
    group = Group(name=name)
    session.add(group)
    session.commit()
    session.refresh(group)
    return GroupOut(id=group.id, name=group.name, created_at=group.created_at)


@router.get("/{group_id}", response_model=GroupDetailOut)
def group_detail(group_id: uuid.UUID, session: Session = Depends(get_session)):
    group = get_group_or_404(session, group_id)
    return _group_detail(session, group)


@router.post("/{group_id}/members", response_model=GroupDetailOut)
def add_member(
    group_id: uuid.UUID,
    body: MemberCreate,
    session: Session = Depends(get_session),
):
    group = get_group_or_404(session, group_id)
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Member name is required")
    existing = {m.name.lower() for m in group_members(session, group_id)}
    if name.lower() in existing:
        raise HTTPException(
            status_code=422, detail=f"'{name}' is already in this group"
        )
    session.add(Member(group_id=group_id, name=name))
    session.commit()
    return _group_detail(session, group)


@router.post("/{group_id}/expenses", response_model=GroupDetailOut)
def add_expense(
    group_id: uuid.UUID,
    body: ExpenseCreate,
    session: Session = Depends(get_session),
):
    group = get_group_or_404(session, group_id)
    try:
        amount_cents = parse_amount(body.amount)
        exact_shares = None
        if body.split_mode == "exact":
            exact_shares = {
                member_id: parse_share(raw)
                for member_id, raw in (body.exact_shares or {}).items()
            }
        record_expense(
            session,
            group_id=group_id,
            description=body.description,
            amount_cents=amount_cents,
            payer_id=body.payer_id,
            participant_ids=body.participant_ids,
            exact_shares=exact_shares,
        )
    except (MoneyError, ExpenseError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _group_detail(session, group)
