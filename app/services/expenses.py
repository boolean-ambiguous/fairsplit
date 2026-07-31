from sqlmodel import Session, select

from app.models import Expense, ExpenseShare, Member


class ExpenseError(ValueError):
    pass


def split_evenly(amount_cents: int, participant_ids: list[int]) -> dict[int, int]:
    """Split amount into integer-cent shares that sum exactly to the total.

    Remainder cents go one each to participants in ascending id order.
    """
    if not participant_ids:
        raise ExpenseError("At least one participant is required")
    ordered = sorted(participant_ids)
    base, remainder = divmod(amount_cents, len(ordered))
    return {
        member_id: base + (1 if i < remainder else 0)
        for i, member_id in enumerate(ordered)
    }


def record_expense(
    session: Session,
    *,
    group_id: int,
    description: str,
    amount_cents: int,
    payer_id: int,
    participant_ids: list[int],
) -> Expense:
    if not description.strip():
        raise ExpenseError("Description is required")
    if amount_cents <= 0:
        raise ExpenseError("Amount must be positive")

    member_ids = set(
        session.exec(select(Member.id).where(Member.group_id == group_id)).all()
    )
    if payer_id not in member_ids:
        raise ExpenseError("Payer must be a member of the group")
    invalid = set(participant_ids) - member_ids
    if invalid:
        raise ExpenseError("All participants must be members of the group")

    shares = split_evenly(amount_cents, participant_ids)

    expense = Expense(
        group_id=group_id,
        description=description.strip(),
        amount_cents=amount_cents,
        payer_id=payer_id,
    )
    session.add(expense)
    session.flush()
    for member_id, share_cents in shares.items():
        session.add(
            ExpenseShare(
                expense_id=expense.id, member_id=member_id, share_cents=share_cents
            )
        )
    session.commit()
    session.refresh(expense)
    return expense
