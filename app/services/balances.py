import uuid

from sqlmodel import Session, func, select

from app.models import Expense, ExpenseShare, Member


def compute_balances(session: Session, group_id: uuid.UUID) -> dict[uuid.UUID, int]:
    """Net cents per member: positive = group owes them, negative = they owe."""
    member_ids = session.exec(
        select(Member.id).where(Member.group_id == group_id)
    ).all()
    balances: dict[uuid.UUID, int] = {mid: 0 for mid in member_ids}

    paid = session.exec(
        select(Expense.payer_id, func.sum(Expense.amount_cents))
        .where(Expense.group_id == group_id)
        .group_by(Expense.payer_id)
    ).all()
    for member_id, total in paid:
        balances[member_id] += total

    owed = session.exec(
        select(ExpenseShare.member_id, func.sum(ExpenseShare.share_cents))
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id)
        .group_by(ExpenseShare.member_id)
    ).all()
    for member_id, total in owed:
        balances[member_id] -= total

    return balances
