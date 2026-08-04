import uuid

from sqlmodel import Session, select

from app.models import MagicLinkToken, Member, User


def latest_token(engine, email):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        assert user is not None
        return session.exec(
            select(MagicLinkToken)
            .where(MagicLinkToken.user_id == user.id)
            .order_by(MagicLinkToken.created_at.desc())
        ).first()


def test_signup_creates_user_and_token(client, engine):
    resp = client.post("/api/auth/signup", json={"email": "Ana@Example.com"})
    assert resp.status_code == 202
    token = latest_token(engine, "ana@example.com")
    assert token is not None
    assert token.consumed_at is None


def test_signup_has_no_format_validation(client):
    # Explicit product decision: magic-link delivery is the validation.
    resp = client.post("/api/auth/signup", json={"email": "not-an-email-but-ok"})
    assert resp.status_code == 202


def test_verify_consumes_token_and_sets_session(client, engine):
    client.post("/api/auth/signup", json={"email": "ana@example.com"})
    token = latest_token(engine, "ana@example.com")

    resp = client.post("/api/auth/verify", json={"token": token.token})
    assert resp.status_code == 200
    assert resp.json()["name"] is None
    assert "fairsplit_session" in resp.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"


def test_verify_rejects_reused_token(client, engine):
    client.post("/api/auth/signup", json={"email": "ana@example.com"})
    token = latest_token(engine, "ana@example.com")
    first = client.post("/api/auth/verify", json={"token": token.token})
    assert first.status_code == 200
    second = client.post("/api/auth/verify", json={"token": token.token})
    assert second.status_code == 400


def test_verify_rejects_unknown_token(client):
    resp = client.post("/api/auth/verify", json={"token": "not-a-real-token"})
    assert resp.status_code == 400


def test_me_requires_session(client):
    assert client.get("/api/auth/me").status_code == 401


def test_name_step_sets_name(client, engine):
    client.post("/api/auth/signup", json={"email": "ana@example.com"})
    token = latest_token(engine, "ana@example.com")
    client.post("/api/auth/verify", json={"token": token.token})

    resp = client.post("/api/auth/name", json={"name": "Ana"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Ana"


def test_blank_name_rejected(client, engine):
    client.post("/api/auth/signup", json={"email": "ana@example.com"})
    token = latest_token(engine, "ana@example.com")
    client.post("/api/auth/verify", json={"token": token.token})
    resp = client.post("/api/auth/name", json={"name": "   "})
    assert resp.status_code == 422


def test_theme_toggle_persists(client, signed_in):
    signed_in("Ana")
    resp = client.patch("/api/auth/me", json={"theme": "light"})
    assert resp.status_code == 200
    assert resp.json()["theme"] == "light"
    assert client.get("/api/auth/me").json()["theme"] == "light"


def test_invalid_theme_rejected(client, signed_in):
    signed_in("Ana")
    resp = client.patch("/api/auth/me", json={"theme": "purple"})
    assert resp.status_code == 422


def test_logout_clears_session(client, signed_in):
    signed_in("Ana")
    assert client.get("/api/auth/me").status_code == 200
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_invited_placeholder_links_to_account_on_verify(client, engine, signed_in):
    signed_in("Ana", email="ana@example.com")
    resp = client.post(
        "/api/groups",
        json={
            "name": "Trip",
            "currency": "USD",
            "invites": [{"name": "Ben", "email": "ben@example.com"}],
        },
    )
    group_id = resp.json()["id"]
    detail = client.get(f"/api/groups/{group_id}").json()
    ben_member = next(m for m in detail["members"] if m["name"] == "Ben")
    assert ben_member["user_id"] is None

    with Session(engine) as session:
        member = session.get(Member, uuid.UUID(ben_member["id"]))
        assert member is not None

    # Ben signs up with the matching email — his placeholder membership
    # should link to his account as soon as he verifies.
    client.post("/api/auth/signup", json={"email": "ben@example.com"})
    token = latest_token(engine, "ben@example.com")
    client.post("/api/auth/verify", json={"token": token.token})
    client.post("/api/auth/name", json={"name": "Ben"})

    groups = client.get("/api/groups").json()
    assert any(g["id"] == group_id for g in groups)
