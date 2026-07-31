from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Expense, Group, Member
from app.services.balances import compute_balances
from app.services.expenses import ExpenseError, record_expense
from app.services.settlements import suggest_settlements
from app.services.money import MoneyError, parse_amount, parse_share

router = APIRouter(prefix="/groups")


def get_group_or_404(session: Session, group_id: int) -> Group:
    group = session.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def group_members(session: Session, group_id: int) -> list[Member]:
    return list(
        session.exec(
            select(Member).where(Member.group_id == group_id).order_by(Member.id)
        ).all()
    )


def group_expenses(session: Session, group_id: int) -> list[Expense]:
    return list(
        session.exec(
            select(Expense)
            .where(Expense.group_id == group_id)
            .order_by(Expense.id.desc())
        ).all()
    )


def _templates(request: Request):
    from app.main import templates

    return templates


def _detail_context(session: Session, group: Group) -> dict:
    members = group_members(session, group.id)
    expenses = group_expenses(session, group.id)
    member_names = {m.id: m.name for m in members}
    balances = compute_balances(session, group.id)
    return {
        "group": group,
        "members": members,
        "expenses": expenses,
        "member_names": member_names,
        "balances": balances,
        "settlements": suggest_settlements(balances),
    }


@router.get("", response_class=HTMLResponse)
def list_groups(request: Request, session: Session = Depends(get_session)):
    groups = session.exec(select(Group).order_by(Group.id)).all()
    return _templates(request).TemplateResponse(
        request, "group_list.html", {"groups": groups}
    )


@router.post("", response_class=HTMLResponse)
def create_group(
    request: Request, name: str = Form(""), session: Session = Depends(get_session)
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Group name is required")
    group = Group(name=name)
    session.add(group)
    session.commit()
    groups = session.exec(select(Group).order_by(Group.id)).all()
    return _templates(request).TemplateResponse(
        request, "_group_list_items.html", {"groups": groups}
    )


@router.get("/{group_id}", response_class=HTMLResponse)
def group_detail(
    request: Request, group_id: int, session: Session = Depends(get_session)
):
    group = get_group_or_404(session, group_id)
    return _templates(request).TemplateResponse(
        request, "group_detail.html", _detail_context(session, group)
    )


@router.post("/{group_id}/members", response_class=HTMLResponse)
def add_member(
    request: Request,
    group_id: int,
    name: str = Form(""),
    session: Session = Depends(get_session),
):
    group = get_group_or_404(session, group_id)
    name = name.strip()
    error = None
    if not name:
        error = "Member name is required"
    else:
        existing = {m.name.lower() for m in group_members(session, group_id)}
        if name.lower() in existing:
            error = f"'{name}' is already in this group"
    if error is None:
        session.add(Member(group_id=group_id, name=name))
        session.commit()
    context = _detail_context(session, group)
    context["member_error"] = error
    context["oob"] = True
    return _templates(request).TemplateResponse(
        request, "_members.html", context, status_code=422 if error else 200
    )


@router.post("/{group_id}/expenses", response_class=HTMLResponse)
async def add_expense(
    request: Request,
    group_id: int,
    description: str = Form(""),
    amount: str = Form(""),
    payer_id: int = Form(...),
    participants: list[int] = Form(default=[]),
    split_mode: str = Form("even"),
    session: Session = Depends(get_session),
):
    group = get_group_or_404(session, group_id)
    error = None
    try:
        amount_cents = parse_amount(amount)
        exact_shares = None
        if split_mode == "exact":
            form = await request.form()
            exact_shares = {}
            for member_id in participants:
                raw = str(form.get(f"share_{member_id}", "")).strip()
                exact_shares[member_id] = parse_share(raw)
        record_expense(
            session,
            group_id=group_id,
            description=description,
            amount_cents=amount_cents,
            payer_id=payer_id,
            participant_ids=participants,
            exact_shares=exact_shares,
        )
    except (MoneyError, ExpenseError) as exc:
        error = str(exc)
    context = _detail_context(session, group)
    context["expense_error"] = error
    context["oob"] = True
    return _templates(request).TemplateResponse(
        request, "_expenses.html", context, status_code=422 if error else 200
    )
