import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    Expense,
    ExpenseHistoryEntry,
    ExpenseShare,
    Group,
    Member,
    Settlement,
    User,
)
from app.schemas import (
    CURRENCIES,
    BalanceOut,
    ExpenseCreate,
    ExpenseHistoryChange,
    ExpenseHistoryEntryOut,
    ExpenseOut,
    ExpenseUpdate,
    GroupCreate,
    GroupDetailOut,
    GroupOut,
    GroupUpdate,
    MemberCreate,
    MemberOut,
    MemberUpdate,
    SettlementCreate,
    SettlementRecordOut,
    SuggestedPaymentOut,
)
from app.services.auth import get_current_user
from app.services.balances import (
    compute_counterparty_balances,
    compute_outstanding_balances,
)
from app.services.expenses import (
    ExpenseError,
    expense_shares,
    record_expense,
    update_expense,
)
from app.services.money import MoneyError, format_cents, parse_amount, parse_share
from app.services.settlements import suggest_settlements

router = APIRouter(prefix="/api/groups")

MAX_PHOTO_LEN = 2_000_000  # base64 data URL length cap (~1.5MB image)


def _validated_photo(data_url: str | None) -> str | None:
    if not data_url:
        return None
    if not data_url.startswith("data:image/"):
        raise HTTPException(status_code=422, detail="Photo must be an image")
    if len(data_url) > MAX_PHOTO_LEN:
        raise HTTPException(status_code=422, detail="Photo is too large")
    return data_url


def get_group_or_404(session: Session, group_id: uuid.UUID) -> Group:
    group = session.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def group_members(session: Session, group_id: uuid.UUID) -> list[Member]:
    return list(
        session.exec(
            select(Member).where(Member.group_id == group_id).order_by(Member.created_at)
        ).all()
    )


def group_expenses(session: Session, group_id: uuid.UUID) -> list[Expense]:
    return list(
        session.exec(
            select(Expense)
            .where(Expense.group_id == group_id)
            .order_by(Expense.date.desc(), Expense.created_at.desc())
        ).all()
    )


def require_membership(session: Session, group_id: uuid.UUID, user: User) -> Member:
    member = session.exec(
        select(Member).where(Member.group_id == group_id, Member.user_id == user.id)
    ).first()
    if member is None:
        raise HTTPException(status_code=403, detail="You're not a member of this group")
    return member


def _find_linked_user(session: Session, email: str | None) -> User | None:
    if not email:
        return None
    return session.exec(select(User).where(User.email == email.strip().lower())).first()


def _history_entries(session: Session, expense_id: uuid.UUID) -> list[ExpenseHistoryEntryOut]:
    rows = session.exec(
        select(ExpenseHistoryEntry)
        .where(ExpenseHistoryEntry.expense_id == expense_id)
        .order_by(ExpenseHistoryEntry.changed_at)
    ).all()
    return [
        ExpenseHistoryEntryOut(
            changed_by=row.changed_by,
            changed_at=row.changed_at,
            changes=[ExpenseHistoryChange(**c) for c in json.loads(row.changes_json)],
        )
        for row in rows
    ]


def _expense_out(session: Session, expense: Expense, my_member_id: uuid.UUID | None) -> ExpenseOut:
    shares = expense_shares(session, expense.id)
    return ExpenseOut(
        id=expense.id,
        description=expense.description,
        amount_cents=expense.amount_cents,
        payer_id=expense.payer_id,
        date=expense.date.date(),
        notes=expense.notes,
        receipt_data_url=expense.receipt_data_url,
        split_mode=expense.split_mode,
        participant_ids=list(shares.keys()),
        shares=shares,
        created_by=expense.created_by,
        created_at=expense.created_at,
        updated_by=expense.updated_by,
        updated_at=expense.updated_at,
        can_delete=my_member_id is not None and expense.payer_id == my_member_id,
        history=_history_entries(session, expense.id),
    )


def _group_detail(session: Session, group: Group, current_user: User) -> GroupDetailOut:
    members = group_members(session, group.id)
    my_member = next((m for m in members if m.user_id == current_user.id), None)
    my_member_id = my_member.id if my_member else None
    expenses = group_expenses(session, group.id)
    outstanding = compute_outstanding_balances(session, group.id)
    suggested = suggest_settlements(outstanding)
    settlement_rows = session.exec(
        select(Settlement)
        .where(Settlement.group_id == group.id)
        .order_by(Settlement.settled_at.desc())
    ).all()
    my_positions = (
        compute_counterparty_balances(session, group.id, my_member_id) if my_member_id else {}
    )
    return GroupDetailOut(
        id=group.id,
        name=group.name,
        currency=group.currency,
        photo_data_url=group.photo_data_url,
        created_at=group.created_at,
        members=[
            MemberOut(id=m.id, name=m.name, email=m.email, user_id=m.user_id, created_at=m.created_at)
            for m in members
        ],
        expenses=[_expense_out(session, e, my_member_id) for e in expenses],
        balances=[BalanceOut(member_id=mid, balance_cents=cents) for mid, cents in outstanding.items()],
        my_positions=[BalanceOut(member_id=mid, balance_cents=cents) for mid, cents in my_positions.items()],
        suggested_settlements=[
            SuggestedPaymentOut(from_member=p.from_member, to_member=p.to_member, amount_cents=p.amount_cents)
            for p in suggested
        ],
        settlement_history=[
            SettlementRecordOut(
                id=s.id,
                from_member=s.from_member,
                to_member=s.to_member,
                amount_cents=s.amount_cents,
                recorded_by=s.recorded_by,
                settled_at=s.settled_at,
            )
            for s in settlement_rows
        ],
    )


@router.get("", response_model=list[GroupOut])
def list_groups(
    session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    my_memberships = session.exec(
        select(Member).where(Member.user_id == current_user.id)
    ).all()
    if not my_memberships:
        return []
    group_ids = [m.group_id for m in my_memberships]
    groups_by_id = {
        g.id: g for g in session.exec(select(Group).where(Group.id.in_(group_ids))).all()
    }
    out = []
    for m in sorted(my_memberships, key=lambda m: groups_by_id[m.group_id].created_at, reverse=True):
        group = groups_by_id.get(m.group_id)
        if group is None:
            continue
        balance = compute_outstanding_balances(session, group.id).get(m.id, 0)
        out.append(
            GroupOut(
                id=group.id,
                name=group.name,
                currency=group.currency,
                photo_data_url=group.photo_data_url,
                created_at=group.created_at,
                member_count=len(group_members(session, group.id)),
                balance_cents=balance,
            )
        )
    return out


@router.post("", response_model=GroupOut, status_code=201)
def create_group(
    body: GroupCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Group name is required")
    if body.currency not in CURRENCIES:
        raise HTTPException(status_code=422, detail="Unsupported currency")
    if not current_user.name:
        raise HTTPException(status_code=422, detail="Set your name before creating a group")

    group = Group(name=name, currency=body.currency, photo_data_url=_validated_photo(body.photo_data_url))
    session.add(group)
    session.flush()

    session.add(
        Member(
            group_id=group.id,
            user_id=current_user.id,
            name=current_user.name,
            email=current_user.email,
        )
    )
    member_count = 1
    existing_names = {current_user.name.lower()}
    for invite in body.invites:
        invite_name = invite.name.strip()
        if not invite_name or invite_name.lower() in existing_names:
            continue
        existing_names.add(invite_name.lower())
        invite_email = (invite.email or "").strip() or None
        linked = _find_linked_user(session, invite_email)
        session.add(
            Member(
                group_id=group.id,
                user_id=linked.id if linked else None,
                name=invite_name,
                email=invite_email,
            )
        )
        member_count += 1

    session.commit()
    session.refresh(group)
    return GroupOut(
        id=group.id,
        name=group.name,
        currency=group.currency,
        photo_data_url=group.photo_data_url,
        created_at=group.created_at,
        member_count=member_count,
        balance_cents=0,
    )


@router.get("/{group_id}", response_model=GroupDetailOut)
def group_detail(
    group_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    require_membership(session, group_id, current_user)
    return _group_detail(session, group, current_user)


@router.patch("/{group_id}", response_model=GroupDetailOut)
def edit_group(
    group_id: uuid.UUID,
    body: GroupUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    require_membership(session, group_id, current_user)

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Group name is required")
        group.name = name
    if body.currency is not None:
        if body.currency not in CURRENCIES:
            raise HTTPException(status_code=422, detail="Unsupported currency")
        group.currency = body.currency
    if body.photo_data_url is not None:
        group.photo_data_url = _validated_photo(body.photo_data_url)

    session.add(group)
    session.commit()
    return _group_detail(session, group, current_user)


@router.post("/{group_id}/members", response_model=GroupDetailOut)
def add_member(
    group_id: uuid.UUID,
    body: MemberCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    require_membership(session, group_id, current_user)
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Member name is required")
    existing = {m.name.lower() for m in group_members(session, group_id)}
    if name.lower() in existing:
        raise HTTPException(status_code=422, detail=f"'{name}' is already in this group")
    email = (body.email or "").strip() or None
    linked = _find_linked_user(session, email)
    session.add(
        Member(group_id=group_id, user_id=linked.id if linked else None, name=name, email=email)
    )
    session.commit()
    return _group_detail(session, group, current_user)


@router.patch("/{group_id}/members/{member_id}", response_model=GroupDetailOut)
def rename_member(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    body: MemberUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    require_membership(session, group_id, current_user)
    member = session.get(Member, member_id)
    if member is None or member.group_id != group_id:
        raise HTTPException(status_code=404, detail="Member not found")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Member name is required")
    existing = {
        m.name.lower() for m in group_members(session, group_id) if m.id != member_id
    }
    if name.lower() in existing:
        raise HTTPException(status_code=422, detail=f"'{name}' is already in this group")
    member.name = name
    session.add(member)
    session.commit()
    return _group_detail(session, group, current_user)


@router.delete("/{group_id}/members/{member_id}", response_model=GroupDetailOut)
def remove_member(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    require_membership(session, group_id, current_user)
    member = session.get(Member, member_id)
    if member is None or member.group_id != group_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.user_id == current_user.id:
        raise HTTPException(status_code=422, detail="You can't remove yourself from a group")

    has_expense_history = session.exec(
        select(Expense.id).where(Expense.group_id == group_id, Expense.payer_id == member_id)
    ).first()
    has_shares = session.exec(
        select(ExpenseShare.id)
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id, ExpenseShare.member_id == member_id)
    ).first()
    has_settlements = session.exec(
        select(Settlement.id).where(
            Settlement.group_id == group_id,
            (Settlement.from_member == member_id) | (Settlement.to_member == member_id),
        )
    ).first()
    if has_expense_history or has_shares or has_settlements:
        raise HTTPException(
            status_code=422,
            detail="Can't remove a member with expense history in this group",
        )

    session.delete(member)
    session.commit()
    return _group_detail(session, group, current_user)


@router.post("/{group_id}/expenses", response_model=GroupDetailOut)
def add_expense(
    group_id: uuid.UUID,
    body: ExpenseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    me = require_membership(session, group_id, current_user)
    try:
        amount_cents = parse_amount(body.amount)
        exact_shares = None
        if body.split_mode == "exact":
            exact_shares = {
                member_id: parse_share(raw) for member_id, raw in (body.exact_shares or {}).items()
            }
        record_expense(
            session,
            group_id=group_id,
            description=body.description,
            amount_cents=amount_cents,
            payer_id=body.payer_id,
            expense_date=body.date,
            participant_ids=body.participant_ids,
            created_by=me.id,
            exact_shares=exact_shares,
            notes=body.notes,
            receipt_data_url=_validated_photo(body.receipt_data_url),
        )
    except (MoneyError, ExpenseError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _group_detail(session, group, current_user)


def _member_name(members_by_id: dict, member_id: uuid.UUID) -> str:
    m = members_by_id.get(member_id)
    return m.name if m else "Someone"


def _split_summary(snapshot: dict, members_by_id: dict, currency: str) -> str:
    payer_id = snapshot["payer_id"]
    shares = snapshot["shares"]
    if snapshot["split_mode"] == "even":
        return f"Split equally among {len(shares)} people"
    debts = {mid: amt for mid, amt in shares.items() if mid != payer_id and amt > 0}
    if not debts:
        return "Split by amount"
    if len(debts) == 1:
        ((mid, amt),) = debts.items()
        return (
            f"{_member_name(members_by_id, mid)} owes {_member_name(members_by_id, payer_id)} "
            f"{format_cents(amt)} {currency}"
        )
    return f"Split by amount across {len(debts)} people"


def _diff_expense(old: dict, new: dict, members_by_id: dict, currency: str) -> list[ExpenseHistoryChange]:
    changes: list[ExpenseHistoryChange] = []
    if old["description"] != new["description"]:
        changes.append(ExpenseHistoryChange(field="Description", previous=old["description"], updated=new["description"]))
    if old["amount_cents"] != new["amount_cents"]:
        changes.append(
            ExpenseHistoryChange(
                field="Amount",
                previous=f"{format_cents(old['amount_cents'])} {currency}",
                updated=f"{format_cents(new['amount_cents'])} {currency}",
            )
        )
    if old["date"] != new["date"]:
        changes.append(ExpenseHistoryChange(field="Date", previous=old["date"].isoformat(), updated=new["date"].isoformat()))
    if old["notes"] != new["notes"]:
        changes.append(
            ExpenseHistoryChange(field="Notes", previous=old["notes"] or "(none)", updated=new["notes"] or "(none)")
        )
    if old["payer_id"] != new["payer_id"]:
        changes.append(
            ExpenseHistoryChange(
                field="Paid by",
                previous=_member_name(members_by_id, old["payer_id"]),
                updated=_member_name(members_by_id, new["payer_id"]),
            )
        )
    old_tag = _split_summary(old, members_by_id, currency)
    new_tag = _split_summary(new, members_by_id, currency)
    if old_tag != new_tag:
        changes.append(ExpenseHistoryChange(field="Split", previous=old_tag, updated=new_tag))
    return changes


@router.patch("/{group_id}/expenses/{expense_id}", response_model=GroupDetailOut)
def edit_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    body: ExpenseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    me = require_membership(session, group_id, current_user)
    expense = session.get(Expense, expense_id)
    if expense is None or expense.group_id != group_id:
        raise HTTPException(status_code=404, detail="Expense not found")

    members_by_id = {m.id: m for m in group_members(session, group_id)}
    old_snapshot = {
        "description": expense.description,
        "amount_cents": expense.amount_cents,
        "date": expense.date.date(),
        "notes": expense.notes or "",
        "payer_id": expense.payer_id,
        "split_mode": expense.split_mode,
        "shares": expense_shares(session, expense.id),
    }

    try:
        amount_cents = parse_amount(body.amount)
        exact_shares = None
        if body.split_mode == "exact":
            exact_shares = {
                member_id: parse_share(raw) for member_id, raw in (body.exact_shares or {}).items()
            }
        update_expense(
            session,
            expense=expense,
            description=body.description,
            amount_cents=amount_cents,
            payer_id=body.payer_id,
            expense_date=body.date,
            participant_ids=body.participant_ids,
            updated_by=me.id,
            exact_shares=exact_shares,
            notes=body.notes,
            receipt_data_url=_validated_photo(body.receipt_data_url),
        )
    except (MoneyError, ExpenseError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    new_snapshot = {
        "description": expense.description,
        "amount_cents": expense.amount_cents,
        "date": expense.date.date(),
        "notes": expense.notes or "",
        "payer_id": expense.payer_id,
        "split_mode": expense.split_mode,
        "shares": expense_shares(session, expense.id),
    }
    changes = _diff_expense(old_snapshot, new_snapshot, members_by_id, group.currency)
    if changes:
        session.add(
            ExpenseHistoryEntry(
                expense_id=expense.id,
                changed_by=me.id,
                changes_json=json.dumps([c.model_dump() for c in changes]),
            )
        )
        session.commit()

    return _group_detail(session, group, current_user)


@router.delete("/{group_id}/expenses/{expense_id}", response_model=GroupDetailOut)
def delete_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    me = require_membership(session, group_id, current_user)
    expense = session.get(Expense, expense_id)
    if expense is None or expense.group_id != group_id:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.payer_id != me.id:
        raise HTTPException(status_code=403, detail="Only the person who paid can delete this expense")

    for row in session.exec(select(ExpenseShare).where(ExpenseShare.expense_id == expense.id)).all():
        session.delete(row)
    for row in session.exec(
        select(ExpenseHistoryEntry).where(ExpenseHistoryEntry.expense_id == expense.id)
    ).all():
        session.delete(row)
    session.delete(expense)
    session.commit()
    return _group_detail(session, group, current_user)


@router.post("/{group_id}/settlements", response_model=GroupDetailOut)
def record_settlement(
    group_id: uuid.UUID,
    body: SettlementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    group = get_group_or_404(session, group_id)
    me = require_membership(session, group_id, current_user)
    member_ids = {m.id for m in group_members(session, group_id)}
    if body.from_member not in member_ids or body.to_member not in member_ids:
        raise HTTPException(status_code=422, detail="Both members must belong to this group")
    if body.from_member == body.to_member:
        raise HTTPException(status_code=422, detail="A member can't pay themself")
    try:
        amount_cents = parse_amount(body.amount)
    except MoneyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    session.add(
        Settlement(
            group_id=group_id,
            from_member=body.from_member,
            to_member=body.to_member,
            amount_cents=amount_cents,
            recorded_by=me.id,
        )
    )
    session.commit()
    return _group_detail(session, group, current_user)
