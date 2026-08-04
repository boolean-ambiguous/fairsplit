from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Group, Member, User
from app.schemas import DashboardGroupOut, DashboardOut, FlowPointOut, OpenPositionOut
from app.services.activity import (
    RANGE_DAYS,
    bucket_range,
    find_my_memberships,
    group_summary_order,
    owed_owe_snapshots,
)
from app.services.auth import get_current_user
from app.services.balances import compute_counterparty_balances, compute_outstanding_balances

router = APIRouter(prefix="/api/dashboard")


@router.get("", response_model=DashboardOut)
def get_dashboard(
    range: str = Query("1mo"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if range not in RANGE_DAYS:
        raise HTTPException(status_code=422, detail=f"Unknown range: {range}")

    matching = find_my_memberships(session, current_user.id)
    ordered_group_ids, last_expense = group_summary_order(session, list(matching.keys()))
    groups_by_id = {
        g.id: g
        for g in session.exec(select(Group).where(Group.id.in_(ordered_group_ids))).all()
    }

    dashboard_groups = []
    open_positions: list[OpenPositionOut] = []
    for group_id in ordered_group_ids:
        member_id = matching[group_id]
        group = groups_by_id[group_id]
        balance = compute_outstanding_balances(session, group_id).get(member_id, 0)
        dashboard_groups.append(
            DashboardGroupOut(
                id=group_id,
                name=group.name,
                currency=group.currency,
                photo_data_url=group.photo_data_url,
                last_expense_at=last_expense.get(group_id),
                balance_cents=balance,
            )
        )
        members_by_id = {
            m.id: m
            for m in session.exec(select(Member).where(Member.group_id == group_id)).all()
        }
        positions = compute_counterparty_balances(session, group_id, member_id)
        for other_id, net_cents in positions.items():
            other = members_by_id.get(other_id)
            open_positions.append(
                OpenPositionOut(
                    group_id=group_id,
                    group_name=group.name,
                    currency=group.currency,
                    other_name=other.name if other else "Someone",
                    net_cents=net_cents,
                )
            )

    snapshots = owed_owe_snapshots(session, matching)
    bucketed = bucket_range(snapshots, range)
    flow = [FlowPointOut(date=d, owed_cents=owed, owe_cents=owe) for d, owed, owe in bucketed]

    return DashboardOut(
        name=current_user.name or "",
        groups=dashboard_groups,
        flow=flow,
        open_positions=open_positions,
    )
