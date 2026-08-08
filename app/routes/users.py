from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.schemas import UserSearchOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/users")

SEARCH_LIMIT = 10


@router.get("/search", response_model=list[UserSearchOut])
def search_users(
    q: str = Query(min_length=1, max_length=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = q.strip().lstrip("@").lower()
    if not query:
        return []
    rows = session.exec(
        select(User)
        .where(User.handle.is_not(None))
        .where(User.handle.like(f"%{query}%"))
        .where(User.id != current_user.id)
        .order_by(User.handle)
        .limit(SEARCH_LIMIT)
    ).all()
    return [UserSearchOut(id=u.id, name=u.name, handle=u.handle) for u in rows]
