import logging
import re

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlmodel import Session, select

from app.config import UntrustedRequestOriginError, resolve_frontend_base_url
from app.database import get_session
from app.models import User
from app.schemas import (
    HANDLE_MAX_LEN,
    HANDLE_MIN_LEN,
    THEMES,
    HandleRequest,
    LoginRequest,
    NameRequest,
    SetPasswordRequest,
    SignupRequest,
    UpdateMeRequest,
    UserOut,
    VerifyRequest,
)
from app.services.auth import (
    SESSION_COOKIE,
    AuthError,
    RateLimitedError,
    authenticate_with_password,
    clear_login_session,
    consume_magic_link_token,
    create_login_session,
    get_current_user,
    start_signup,
)
from app.services.email import send_magic_link
from app.services.passwords import hash_password
from app.services.rate_limit import login_ip_limiter, signup_ip_limiter

logger = logging.getLogger("fairsplit.auth")

router = APIRouter(prefix="/api/auth")

HANDLE_PATTERN = re.compile(r"^[a-z0-9_]+$")


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        handle=user.handle,
        theme=user.theme,
        has_password=user.password_hash is not None,
    )


def _normalize_handle(session: Session, current_user: User, raw: str) -> str:
    handle = raw.strip().lstrip("@").lower()
    if len(handle) < HANDLE_MIN_LEN or len(handle) > HANDLE_MAX_LEN or not HANDLE_PATTERN.match(handle):
        raise HTTPException(
            status_code=422,
            detail=f"Handle must be {HANDLE_MIN_LEN}-{HANDLE_MAX_LEN} characters, lowercase letters, numbers, or underscores only",
        )
    existing = session.exec(select(User).where(User.handle == handle)).first()
    if existing is not None and existing.id != current_user.id:
        raise HTTPException(status_code=409, detail="That handle is already taken")
    return handle


@router.post("/signup", status_code=202)
def signup(body: SignupRequest, request: Request, session: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    if not signup_ip_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts, please wait and try again.")
    try:
        user, token = start_signup(session, body.email)
    except RateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except AuthError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        base_url = resolve_frontend_base_url(
            str(request.base_url), request.headers.get("origin")
        )
    except UntrustedRequestOriginError:
        logger.error(
            "Rejected signup: request Host %r is not loopback/private and "
            "FAIRSPLIT_FRONTEND_URL is not set. Set FAIRSPLIT_FRONTEND_URL "
            "to the app's real public URL to fix this.",
            request.headers.get("host"),
        )
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: unable to determine the frontend URL for magic links.",
        )
    link = f"{base_url}/verify?token={token.token}"
    try:
        send_magic_link(user.email, link)
    except Exception:
        logger.exception("Failed to send magic-link email to %s", user.email)
        raise HTTPException(
            status_code=502,
            detail="We couldn't send the sign-in email right now. Please try again shortly.",
        )
    return {"message": "Check your email for a magic link."}


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, request: Request, response: Response, session: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    if not login_ip_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts, please wait and try again.")
    try:
        user = authenticate_with_password(session, body.identifier, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    create_login_session(session, user, response, secure=request.url.scheme == "https")
    return _user_out(user)


@router.post("/password", response_model=UserOut)
def set_password(
    body: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.password_hash = hash_password(body.password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return _user_out(current_user)


@router.post("/verify", response_model=UserOut)
def verify(
    body: VerifyRequest,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):
    try:
        user = consume_magic_link_token(session, body.token)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    create_login_session(session, user, response, secure=request.url.scheme == "https")
    return _user_out(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/name", response_model=UserOut)
def set_name(
    body: NameRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    current_user.name = name
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return _user_out(current_user)


@router.post("/handle", response_model=UserOut)
def set_handle(
    body: HandleRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.handle = _normalize_handle(session, current_user, body.handle)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return _user_out(current_user)


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Name is required")
        current_user.name = name
    if body.handle is not None:
        current_user.handle = _normalize_handle(session, current_user, body.handle)
    if body.theme is not None:
        if body.theme not in THEMES:
            raise HTTPException(status_code=422, detail="Theme must be 'system', 'light', or 'dark'")
        current_user.theme = body.theme
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return _user_out(current_user)


@router.post("/logout")
def logout(
    response: Response,
    session: Session = Depends(get_session),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    clear_login_session(session, session_token, response)
    return {"ok": True}
