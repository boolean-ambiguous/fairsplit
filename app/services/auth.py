import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.database import get_session
from app.models import LoginSession, MagicLinkToken, Member, User, utcnow

SESSION_COOKIE = "fairsplit_session"
MAGIC_LINK_TTL = timedelta(minutes=30)
SESSION_TTL = timedelta(days=30)
MAGIC_LINK_RATE_LIMIT = 3
MAGIC_LINK_RATE_WINDOW = timedelta(minutes=15)


def _aware(dt: datetime) -> datetime:
    """SQLite round-trips datetimes as naive, dropping tzinfo — normalize
    back to UTC-aware before comparing against a fresh `utcnow()`."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class AuthError(ValueError):
    pass


class RateLimitedError(AuthError):
    pass


def start_signup(session: Session, email: str) -> tuple[User, MagicLinkToken]:
    email = email.strip()
    if not email:
        raise AuthError("Email is required")
    email_key = email.lower()
    user = session.exec(select(User).where(User.email == email_key)).first()
    if user is None:
        user = User(email=email_key)
        session.add(user)
        session.commit()
        session.refresh(user)
    recent_tokens = session.exec(
        select(MagicLinkToken).where(MagicLinkToken.user_id == user.id)
    ).all()
    window_start = utcnow() - MAGIC_LINK_RATE_WINDOW
    recent_count = sum(1 for t in recent_tokens if _aware(t.created_at) > window_start)
    if recent_count >= MAGIC_LINK_RATE_LIMIT:
        raise RateLimitedError("Too many sign-in attempts. Please wait a few minutes and try again.")
    token = MagicLinkToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        expires_at=utcnow() + MAGIC_LINK_TTL,
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return user, token


def consume_magic_link_token(session: Session, raw_token: str) -> User:
    token = session.exec(
        select(MagicLinkToken).where(MagicLinkToken.token == raw_token)
    ).first()
    if token is None or token.consumed_at is not None or _aware(token.expires_at) < utcnow():
        raise AuthError("This link is invalid or has expired.")
    token.consumed_at = utcnow()
    session.add(token)
    user = session.get(User, token.user_id)
    if user is None:
        raise AuthError("This link is invalid or has expired.")
    _link_invited_memberships(session, user)
    session.commit()
    return user


def _link_invited_memberships(session: Session, user: User) -> None:
    """Attach any placeholder memberships — added by name+email at group
    creation/invite time, before the invitee had an account — to this now
    -verified user, so their groups show up on their dashboard."""
    placeholders = session.exec(
        select(Member).where(
            Member.user_id.is_(None),  # type: ignore[union-attr]
            Member.email.is_not(None),  # type: ignore[union-attr]
        )
    ).all()
    email_lower = user.email.lower()
    for member in placeholders:
        if member.email and member.email.lower() == email_lower:
            member.user_id = user.id
            session.add(member)


def create_login_session(
    session: Session, user: User, response: Response, *, secure: bool
) -> LoginSession:
    login_session = LoginSession(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        expires_at=utcnow() + SESSION_TTL,
    )
    session.add(login_session)
    session.commit()
    session.refresh(login_session)
    response.set_cookie(
        SESSION_COOKIE,
        login_session.token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )
    return login_session


def clear_login_session(session: Session, token: str | None, response: Response) -> None:
    if token:
        existing = session.exec(
            select(LoginSession).where(LoginSession.token == token)
        ).first()
        if existing:
            session.delete(existing)
            session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


def get_current_user(
    session: Session = Depends(get_session),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not signed in")
    login_session = session.exec(
        select(LoginSession).where(LoginSession.token == session_token)
    ).first()
    if login_session is None or _aware(login_session.expires_at) < utcnow():
        raise HTTPException(status_code=401, detail="Session expired")
    user = session.get(User, login_session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user
