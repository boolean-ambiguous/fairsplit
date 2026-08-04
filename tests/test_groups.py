import uuid

from sqlmodel import Session, select

from app.models import MagicLinkToken, User


def test_create_group(client, signed_in):
    signed_in("Ana")
    resp = client.post("/api/groups", json={"name": "Ski trip", "currency": "USD"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ski trip"
    assert body["member_count"] == 1
    assert uuid.UUID(body["id"])

    listing = client.get("/api/groups").json()
    assert any(g["name"] == "Ski trip" for g in listing)


def test_group_creation_requires_login(client):
    resp = client.post("/api/groups", json={"name": "Ski trip"})
    assert resp.status_code == 401


def test_group_creation_requires_name_set(client, engine):
    email = "noname@example.com"
    client.post("/api/auth/signup", json={"email": email})
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        token = session.exec(
            select(MagicLinkToken).where(MagicLinkToken.user_id == user.id)
        ).first()
    verify = client.post("/api/auth/verify", json={"token": token.token})
    assert verify.status_code == 200
    assert verify.json()["name"] is None

    # Verified but skipped the name step — the API still guards it even
    # though the normal UI flow always sets a name right after verifying.
    resp = client.post("/api/groups", json={"name": "Ski trip"})
    assert resp.status_code == 422


def test_blank_group_name_rejected(client, signed_in):
    signed_in("Ana")
    resp = client.post("/api/groups", json={"name": "   "})
    assert resp.status_code == 422


def test_unsupported_currency_rejected(client, signed_in):
    signed_in("Ana")
    resp = client.post("/api/groups", json={"name": "Trip", "currency": "ZZZ"})
    assert resp.status_code == 422


def test_invited_member_added(client, group_with_members):
    group_id = group_with_members(["Ana"])
    resp = client.post(f"/api/groups/{group_id}/members", json={"name": "Ben"})
    assert resp.status_code == 200
    assert {m["name"] for m in resp.json()["members"]} == {"Ana", "Ben"}


def test_group_with_members_helper_invites_at_creation(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    detail = client.get(f"/api/groups/{group_id}").json()
    assert {m["name"] for m in detail["members"]} == {"Ana", "Ben"}


def test_duplicate_member_rejected(client, group_with_members):
    group_id = group_with_members(["Ana"])
    resp = client.post(f"/api/groups/{group_id}/members", json={"name": "ana"})
    assert resp.status_code == 422
    assert "already in this group" in resp.json()["detail"]


def test_unknown_group_404(client, signed_in):
    signed_in("Ana")
    assert client.get(f"/api/groups/{uuid.uuid4()}").status_code == 404


def test_non_member_forbidden(client, signed_in, group_with_members):
    group_id = group_with_members(["Ana"])
    signed_in("Ben")
    assert client.get(f"/api/groups/{group_id}").status_code == 403


def test_malformed_group_id_rejected_before_lookup(client, signed_in):
    signed_in("Ana")
    resp = client.get("/api/groups/not-a-uuid")
    assert resp.status_code == 422


def test_edit_group_name_and_currency(client, group_with_members):
    group_id = group_with_members(["Ana"])
    resp = client.patch(
        f"/api/groups/{group_id}", json={"name": "Renamed", "currency": "EUR"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed"
    assert body["currency"] == "EUR"


def test_rename_member(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    ben_id = group_with_members.member_ids["Ben"]
    resp = client.patch(f"/api/groups/{group_id}/members/{ben_id}", json={"name": "Benjamin"})
    assert resp.status_code == 200
    assert {m["name"] for m in resp.json()["members"]} == {"Ana", "Benjamin"}


def test_rename_member_rejects_duplicate(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    ben_id = group_with_members.member_ids["Ben"]
    resp = client.patch(f"/api/groups/{group_id}/members/{ben_id}", json={"name": "ana"})
    assert resp.status_code == 422


def test_remove_member_without_history(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    ben_id = group_with_members.member_ids["Ben"]
    resp = client.delete(f"/api/groups/{group_id}/members/{ben_id}")
    assert resp.status_code == 200
    assert {m["name"] for m in resp.json()["members"]} == {"Ana"}


def test_remove_member_with_expense_history_rejected(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    ana_id = group_with_members.member_ids["Ana"]
    ben_id = group_with_members.member_ids["Ben"]
    client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Lunch",
            "amount": "10.00",
            "date": "2024-01-01",
            "payer_id": str(ana_id),
            "participant_ids": [str(ana_id), str(ben_id)],
        },
    )
    resp = client.delete(f"/api/groups/{group_id}/members/{ben_id}")
    assert resp.status_code == 422


def test_remove_self_rejected(client, group_with_members):
    group_id = group_with_members(["Ana"])
    ana_id = group_with_members.member_ids["Ana"]
    resp = client.delete(f"/api/groups/{group_id}/members/{ana_id}")
    assert resp.status_code == 422
