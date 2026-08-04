import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models import Expense, ExpenseShare, Group, Member, Settlement

FIXED_RANGE_DAYS = {"1mo": 30, "12mo": 365}
RANGE_KEYS = {*FIXED_RANGE_DAYS, "all"}


def find_my_memberships(session: Session, user_id: uuid.UUID) -> dict[uuid.UUID, uuid.UUID]:
    """group_id -> my member_id, for every group this user belongs to."""
    members = session.exec(select(Member).where(Member.user_id == user_id)).all()
    return {m.group_id: m.id for m in members}


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


def _timeline_events(session: Session, group_ids: list[uuid.UUID]) -> list[tuple]:
    """All expense/settlement events across the given groups, oldest first."""
    if not group_ids:
        return []
    expenses = session.exec(select(Expense).where(Expense.group_id.in_(group_ids))).all()
    expense_ids = [e.id for e in expenses]
    shares = (
        session.exec(
            select(ExpenseShare).where(ExpenseShare.expense_id.in_(expense_ids))
        ).all()
        if expense_ids
        else []
    )
    shares_by_expense: dict[uuid.UUID, list[ExpenseShare]] = defaultdict(list)
    for s in shares:
        shares_by_expense[s.expense_id].append(s)

    events = [
        (e.date.date(), e.group_id, "expense", (e, shares_by_expense.get(e.id, [])))
        for e in expenses
    ]
    settlements = session.exec(
        select(Settlement).where(Settlement.group_id.in_(group_ids))
    ).all()
    events += [(s.settled_at.date(), s.group_id, "settlement", s) for s in settlements]
    events.sort(key=lambda ev: ev[0])
    return events


def _record(net: dict[uuid.UUID, int], my_id, debtor, creditor, amt: int) -> None:
    if creditor == my_id and debtor != my_id:
        net[debtor] = net.get(debtor, 0) + amt
    elif debtor == my_id and creditor != my_id:
        net[creditor] = net.get(creditor, 0) - amt


def _totals(net_by_group: dict[uuid.UUID, dict[uuid.UUID, int]]) -> tuple[int, int]:
    owed = owe = 0
    for net in net_by_group.values():
        for amt in net.values():
            if amt > 0:
                owed += amt
            elif amt < 0:
                owe += -amt
    return owed, owe


def owed_owe_snapshots(
    session: Session, matching: dict[uuid.UUID, uuid.UUID]
) -> list[tuple[date, int, int]]:
    """One (date, owed_cents, owe_cents) snapshot per distinct calendar day
    that had expense/settlement activity across the user's groups, in
    chronological order. owed/owe are cumulative, gross totals as of end of
    that day: owed = sum of positive per-counterparty balances across every
    group, owe = sum of the absolute value of negative ones — summed across
    groups and counterparties, not netted against each other (a $50 credit
    in one group and a $20 debt in another both show up, rather than
    collapsing to a single +$30). See
    `balances.compute_counterparty_balances` for the per-expense threading
    rule; this applies the same rule incrementally over time.
    """
    events = _timeline_events(session, list(matching.keys()))
    net_by_group: dict[uuid.UUID, dict[uuid.UUID, int]] = defaultdict(dict)

    snapshots: list[tuple[date, int, int]] = []
    current_day: date | None = None
    for event_date, group_id, kind, payload in events:
        if current_day is not None and event_date != current_day:
            snapshots.append((current_day, *_totals(net_by_group)))
        current_day = event_date

        my_id = matching[group_id]
        net = net_by_group[group_id]
        if kind == "expense":
            expense, shares = payload
            for share in shares:
                if share.member_id == expense.payer_id:
                    continue
                _record(net, my_id, share.member_id, expense.payer_id, share.share_cents)
        else:
            settlement: Settlement = payload
            _record(net, my_id, settlement.from_member, settlement.to_member, -settlement.amount_cents)

    if current_day is not None:
        snapshots.append((current_day, *_totals(net_by_group)))
    return snapshots


def bucket_range(
    snapshots: list[tuple[date, int, int]], range_key: str
) -> list[tuple[date, int, int]]:
    """One point per calendar day in the trailing `range_key` window ending
    today (UTC) — `"1mo"`/`"12mo"` use a fixed day count, `"all"` instead
    starts at the earliest snapshot (or today, if there are none yet).
    Each day carries the most recent snapshot at or before it
    (forward-filled — owed/owe are cumulative state, not daily deltas, so a
    quiet day repeats yesterday's totals rather than resetting to zero);
    days before any activity read as (0, 0)."""
    today = datetime.now(timezone.utc).date()
    if range_key == "all":
        start = snapshots[0][0] if snapshots else today
    else:
        start = today - timedelta(days=FIXED_RANGE_DAYS[range_key] - 1)
    total_days = (today - start).days + 1

    result: list[tuple[date, int, int]] = []
    idx = 0
    last_owed, last_owe = 0, 0
    for i in range(total_days):
        day = start + timedelta(days=i)
        while idx < len(snapshots) and snapshots[idx][0] <= day:
            last_owed, last_owe = snapshots[idx][1], snapshots[idx][2]
            idx += 1
        result.append((day, last_owed, last_owe))
    return result
