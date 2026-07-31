import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models import Expense, ExpenseShare, Group, Member

RANGE_DAYS = {"1d": 1, "5d": 5, "1mo": 30, "12mo": 365}


def find_matching_members(
    session: Session, nickname: str
) -> dict[uuid.UUID, uuid.UUID]:
    """Map group_id -> member_id for every group where `nickname` matches a
    member case-insensitively. At most one match per group (member names
    are unique per group, case-insensitive, per the groups capability)."""
    nickname_lower = nickname.strip().lower()
    members = session.exec(select(Member)).all()
    return {
        m.group_id: m.id for m in members if m.name.lower() == nickname_lower
    }


def daily_balance_series(
    session: Session, matching: dict[uuid.UUID, uuid.UUID]
) -> dict[date, int]:
    """Net cents per UTC calendar day, summed across every group in
    `matching` (group_id -> my member_id in that group). Each expense's
    contribution to my balance in its group is attributed to the day it
    was recorded. Summed over full history, this equals the sum of
    compute_balances(group)[my_id] across the same groups -- see
    add-dashboard/design.md for why that holds exactly."""
    if not matching:
        return {}

    group_ids = list(matching.keys())
    expenses = session.exec(
        select(Expense).where(Expense.group_id.in_(group_ids))
    ).all()
    shares = session.exec(
        select(ExpenseShare).where(
            ExpenseShare.expense_id.in_([e.id for e in expenses])
        )
    ).all()
    shares_by_expense: dict[uuid.UUID, list[ExpenseShare]] = defaultdict(list)
    for s in shares:
        shares_by_expense[s.expense_id].append(s)

    series: dict[date, int] = defaultdict(int)
    for expense in expenses:
        my_member_id = matching[expense.group_id]
        day = expense.created_at.date()
        if expense.payer_id == my_member_id:
            series[day] += expense.amount_cents
        for share in shares_by_expense.get(expense.id, []):
            if share.member_id == my_member_id:
                series[day] -= share.share_cents

    return dict(series)


def filter_range(series: dict[date, int], range_key: str) -> list[tuple[date, int]]:
    """Pure slice of `series` over the trailing N days ending today (UTC),
    filling zeros for days with no activity. Does not recompute anything."""
    days = RANGE_DAYS[range_key]
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    return [
        (start + timedelta(days=i), series.get(start + timedelta(days=i), 0))
        for i in range(days)
    ]


def group_summary_order(session: Session, group_ids: list[uuid.UUID]):
    """Groups ordered by most-recent-expense desc; groups with no expenses
    sort last, ordered among themselves by group creation time desc."""
    groups = {g.id: g for g in session.exec(select(Group)).all() if g.id in group_ids}
    last_expense: dict[uuid.UUID, datetime] = {}
    for e in session.exec(
        select(Expense).where(Expense.group_id.in_(group_ids))
    ).all():
        current = last_expense.get(e.group_id)
        if current is None or e.created_at > current:
            last_expense[e.group_id] = e.created_at

    def sort_key(group_id: uuid.UUID):
        last = last_expense.get(group_id)
        has_expense = last is not None
        return (
            not has_expense,
            -(last.timestamp() if has_expense else groups[group_id].created_at.timestamp()),
        )

    return sorted(group_ids, key=sort_key), last_expense
