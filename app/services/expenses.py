import uuid
from datetime import date as date_type
from datetime import datetime

from sqlmodel import Session, select

from app.models import Expense, ExpenseShare, Member, utcnow


class ExpenseError(ValueError):
    pass


def split_evenly(
    amount_cents: int, participant_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Split amount into integer-cent shares that sum exactly to the total.

    Remainder cents go one each to the first participants in the given
    order. The caller is responsible for supplying a meaningful order
    (e.g. group join order) — ids carry no inherent ordering of their own.
    """
    if not participant_ids:
        raise ExpenseError("At least one participant is required")
    base, remainder = divmod(amount_cents, len(participant_ids))
    return {
        member_id: base + (1 if i < remainder else 0)
        for i, member_id in enumerate(participant_ids)
    }


def validate_exact_shares(
    amount_cents: int,
    participant_ids: list[uuid.UUID],
    exact_shares: dict[uuid.UUID, int],
) -> dict[uuid.UUID, int]:
    if set(exact_shares) != set(participant_ids):
        raise ExpenseError("Exact shares must cover exactly the participants")
    if any(share < 0 for share in exact_shares.values()):
        raise ExpenseError("Shares cannot be negative")
    total = sum(exact_shares.values())
    if total != amount_cents:
        from app.services.money import format_cents

        diff = amount_cents - total
        direction = "missing" if diff > 0 else "too much"
        raise ExpenseError(
            f"Shares total {format_cents(total)} but the expense is "
            f"{format_cents(amount_cents)} ({format_cents(abs(diff))} {direction})"
        )
    return dict(exact_shares)


def _resolve_shares(
    session: Session,
    group_id: uuid.UUID,
    amount_cents: int,
    payer_id: uuid.UUID,
    participant_ids: list[uuid.UUID],
    exact_shares: dict[uuid.UUID, int] | None,
) -> dict[uuid.UUID, int]:
    members_by_join_order = session.exec(
        select(Member.id).where(Member.group_id == group_id).order_by(Member.created_at)
    ).all()
    member_ids = set(members_by_join_order)
    if payer_id not in member_ids:
        raise ExpenseError("Payer must be a member of the group")
    participant_set = set(participant_ids)
    invalid = participant_set - member_ids
    if invalid:
        raise ExpenseError("All participants must be members of the group")

    if exact_shares is not None:
        return validate_exact_shares(amount_cents, participant_ids, exact_shares)
    ordered_participants = [
        member_id for member_id in members_by_join_order if member_id in participant_set
    ]
    return split_evenly(amount_cents, ordered_participants)


def record_expense(
    session: Session,
    *,
    group_id: uuid.UUID,
    description: str,
    amount_cents: int,
    payer_id: uuid.UUID,
    expense_date: date_type,
    participant_ids: list[uuid.UUID],
    created_by: uuid.UUID,
    exact_shares: dict[uuid.UUID, int] | None = None,
    notes: str | None = None,
    receipt_data_url: str | None = None,
) -> Expense:
    if not description.strip():
        raise ExpenseError("Description is required")
    if amount_cents <= 0:
        raise ExpenseError("Amount must be positive")
    if not participant_ids:
        raise ExpenseError("At least one participant is required")
    if expense_date > datetime.now().date():
        raise ExpenseError("Date cannot be in the future")

    shares = _resolve_shares(
        session, group_id, amount_cents, payer_id, participant_ids, exact_shares
    )

    expense = Expense(
        group_id=group_id,
        description=description.strip(),
        amount_cents=amount_cents,
        payer_id=payer_id,
        split_mode="exact" if exact_shares is not None else "even",
        date=datetime.combine(expense_date, datetime.min.time()),
        notes=(notes or "").strip() or None,
        receipt_data_url=receipt_data_url,
        created_by=created_by,
    )
    session.add(expense)
    session.flush()
    for member_id, share_cents in shares.items():
        session.add(
            ExpenseShare(expense_id=expense.id, member_id=member_id, share_cents=share_cents)
        )
    session.commit()
    session.refresh(expense)
    return expense


def update_expense(
    session: Session,
    *,
    expense: Expense,
    description: str,
    amount_cents: int,
    payer_id: uuid.UUID,
    expense_date: date_type,
    participant_ids: list[uuid.UUID],
    updated_by: uuid.UUID,
    exact_shares: dict[uuid.UUID, int] | None = None,
    notes: str | None = None,
    receipt_data_url: str | None = None,
) -> Expense:
    if not description.strip():
        raise ExpenseError("Description is required")
    if amount_cents <= 0:
        raise ExpenseError("Amount must be positive")
    if not participant_ids:
        raise ExpenseError("At least one participant is required")
    if expense_date > datetime.now().date():
        raise ExpenseError("Date cannot be in the future")

    shares = _resolve_shares(
        session, expense.group_id, amount_cents, payer_id, participant_ids, exact_shares
    )

    expense.description = description.strip()
    expense.amount_cents = amount_cents
    expense.payer_id = payer_id
    expense.split_mode = "exact" if exact_shares is not None else "even"
    expense.date = datetime.combine(expense_date, datetime.min.time())
    expense.notes = (notes or "").strip() or None
    expense.receipt_data_url = receipt_data_url
    expense.updated_by = updated_by
    expense.updated_at = utcnow()
    session.add(expense)

    existing_shares = session.exec(
        select(ExpenseShare).where(ExpenseShare.expense_id == expense.id)
    ).all()
    for row in existing_shares:
        session.delete(row)
    session.flush()
    for member_id, share_cents in shares.items():
        session.add(
            ExpenseShare(expense_id=expense.id, member_id=member_id, share_cents=share_cents)
        )
    session.commit()
    session.refresh(expense)
    return expense


def expense_shares(session: Session, expense_id: uuid.UUID) -> dict[uuid.UUID, int]:
    rows = session.exec(
        select(ExpenseShare).where(ExpenseShare.expense_id == expense_id)
    ).all()
    return {row.member_id: row.share_cents for row in rows}
