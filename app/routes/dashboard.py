from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Group
from app.schemas import DashboardGroupOut, DashboardOut, FlowPointOut
from app.services.activity import (
    RANGE_DAYS,
    daily_balance_series,
    filter_range,
    find_matching_members,
    group_summary_order,
)
from app.services.balances import compute_balances

router = APIRouter(prefix="/api/dashboard")


@router.get("", response_model=DashboardOut)
def get_dashboard(
    nickname: str = Query(...),
    range: str = Query("1mo"),
    session: Session = Depends(get_session),
):
    if not nickname.strip():
        raise HTTPException(status_code=422, detail="Nickname is required")
    if range not in RANGE_DAYS:
        raise HTTPException(status_code=422, detail=f"Unknown range: {range}")

    matching = find_matching_members(session, nickname)
    ordered_group_ids, last_expense = group_summary_order(
        session, list(matching.keys())
    )
    groups_by_id = {
        g.id: g
        for g in session.exec(
            select(Group).where(Group.id.in_(ordered_group_ids))
        ).all()
    }

    dashboard_groups = []
    for group_id in ordered_group_ids:
        member_id = matching[group_id]
        balance = compute_balances(session, group_id).get(member_id, 0)
        dashboard_groups.append(
            DashboardGroupOut(
                id=group_id,
                name=groups_by_id[group_id].name,
                last_expense_at=last_expense.get(group_id),
                balance_cents=balance,
            )
        )

    series = daily_balance_series(session, matching)
    flow = [
        FlowPointOut(date=d, net_cents=cents)
        for d, cents in filter_range(series, range)
    ]

    return DashboardOut(
        nickname=nickname.strip(), groups=dashboard_groups, flow=flow
    )
