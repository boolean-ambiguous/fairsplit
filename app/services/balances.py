import uuid

from sqlmodel import Session, func, select

from app.models import Expense, ExpenseShare, Member, Settlement


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


def compute_outstanding_balances(
    session: Session, group_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    """compute_balances, further offset by recorded ('marked as paid')
    settlements — the balances actually shown to users and fed into
    settlement suggestions."""
    balances = compute_balances(session, group_id)
    settlements = session.exec(
        select(Settlement).where(Settlement.group_id == group_id)
    ).all()
    for s in settlements:
        balances[s.from_member] = balances.get(s.from_member, 0) + s.amount_cents
        balances[s.to_member] = balances.get(s.to_member, 0) - s.amount_cents
    return balances


def compute_counterparty_balances(
    session: Session, group_id: uuid.UUID, my_member_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    """Net cents between `my_member_id` and each other member of the group,
    threaded through whoever paid each expense — the payer is the sole
    counterparty for every other participant's share of that expense, so an
    equal split among four people creates three direct debts to the payer,
    not a tangle of debts between every pair. Recorded settlements offset
    the same way. Positive = that member owes me; negative = I owe them.
    Members I've never directly owed or been owed by don't appear."""
    net: dict[uuid.UUID, int] = {}

    def record(debtor: uuid.UUID, creditor: uuid.UUID, amt: int) -> None:
        if creditor == my_member_id and debtor != my_member_id:
            net[debtor] = net.get(debtor, 0) + amt
        elif debtor == my_member_id and creditor != my_member_id:
            net[creditor] = net.get(creditor, 0) - amt

    expenses = session.exec(select(Expense).where(Expense.group_id == group_id)).all()
    expense_ids = [e.id for e in expenses]
    shares = (
        session.exec(
            select(ExpenseShare).where(ExpenseShare.expense_id.in_(expense_ids))
        ).all()
        if expense_ids
        else []
    )
    shares_by_expense: dict[uuid.UUID, list[ExpenseShare]] = {}
    for s in shares:
        shares_by_expense.setdefault(s.expense_id, []).append(s)

    for e in expenses:
        for share in shares_by_expense.get(e.id, []):
            if share.member_id == e.payer_id:
                continue
            record(share.member_id, e.payer_id, share.share_cents)

    settlements = session.exec(
        select(Settlement).where(Settlement.group_id == group_id)
    ).all()
    for s in settlements:
        record(s.from_member, s.to_member, -s.amount_cents)

    return {mid: amt for mid, amt in net.items() if amt != 0}
