import random
import uuid
from datetime import date, timedelta

import pytest
from sqlmodel import Session

from app.services.activity import (
    bucket_range,
    find_my_memberships,
    group_summary_order,
    owed_owe_snapshots,
)
from app.services.balances import compute_counterparty_balances

TODAY = date.today().isoformat()


def create_group(client, name, invites=None):
    resp = client.post(
        "/api/groups", json={"name": name, "currency": "USD", "invites": invites or []}
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


def my_member_id(client, group_id):
    detail = client.get(f"/api/groups/{group_id}").json()
    return uuid.UUID(next(m["id"] for m in detail["members"] if m["user_id"] is not None))


def add_expense(client, group_id, payer_id, participant_ids, amount="10.00"):
    return client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Expense",
            "amount": amount,
            "date": TODAY,
            "payer_id": str(payer_id),
            "participant_ids": [str(p) for p in participant_ids],
        },
    )


def test_find_my_memberships_scoped_to_user(client, engine, signed_in):
    signed_in("Ana")
    g1 = create_group(client, "Trip A")
    signed_in("Ben")
    g2 = create_group(client, "Trip B")

    with Session(engine) as session:
        from app.models import User
        from sqlmodel import select

        ana_id = session.exec(select(User).where(User.email == "ana@example.com")).first().id
        matching = find_my_memberships(session, ana_id)
    assert set(matching.keys()) == {g1}


def test_group_ordering_active_groups_first(client, engine, signed_in):
    signed_in("Ana")
    older = create_group(client, "Older activity")
    newer = create_group(client, "Newer activity")
    add_expense(client, older, my_member_id(client, older), [my_member_id(client, older)])
    add_expense(client, newer, my_member_id(client, newer), [my_member_id(client, newer)])

    with Session(engine) as session:
        ordered, _ = group_summary_order(session, [older, newer])
    assert ordered == [newer, older]


def test_group_ordering_inactive_groups_last(client, engine, signed_in):
    signed_in("Ana")
    active = create_group(client, "Active")
    inactive = create_group(client, "Inactive")
    add_expense(client, active, my_member_id(client, active), [my_member_id(client, active)])

    with Session(engine) as session:
        ordered, _ = group_summary_order(session, [inactive, active])
    assert ordered == [active, inactive]


def test_dashboard_endpoint_returns_ordered_groups_and_balances(client, signed_in):
    signed_in("Ana", email="ana@example.com")
    g1 = create_group(client, "Trip A", invites=[{"name": "Ben", "email": "ben@example.com"}])
    detail = client.get(f"/api/groups/{g1}").json()
    ana = uuid.UUID(next(m["id"] for m in detail["members"] if m["name"] == "Ana"))
    ben = uuid.UUID(next(m["id"] for m in detail["members"] if m["name"] == "Ben"))
    add_expense(client, g1, ana, [ana, ben], amount="20.00")

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["groups"][0]["name"] == "Trip A"
    assert body["groups"][0]["balance_cents"] == 1000


def test_dashboard_requires_login(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 401


def test_dashboard_rejects_unknown_range(client, signed_in):
    signed_in("Ana")
    resp = client.get("/api/dashboard", params={"range": "bogus"})
    assert resp.status_code == 422


def test_dashboard_open_positions_reflect_counterparties(client, signed_in):
    signed_in("Ana", email="ana@example.com")
    g1 = create_group(client, "Trip A", invites=[{"name": "Ben", "email": "ben@example.com"}])
    detail = client.get(f"/api/groups/{g1}").json()
    ana = uuid.UUID(next(m["id"] for m in detail["members"] if m["name"] == "Ana"))
    ben = uuid.UUID(next(m["id"] for m in detail["members"] if m["name"] == "Ben"))
    add_expense(client, g1, ana, [ana, ben], amount="20.00")

    resp = client.get("/api/dashboard")
    positions = resp.json()["open_positions"]
    assert len(positions) == 1
    assert positions[0]["other_name"] == "Ben"
    assert positions[0]["net_cents"] == 1000


def test_owed_owe_snapshots_last_point_matches_current_aggregate(client, engine, signed_in):
    signed_in("Ana", email="ana@example.com")
    g1 = create_group(client, "Group 1", invites=[{"name": "Ben", "email": "ben@example.com"}])
    g2 = create_group(client, "Group 2", invites=[{"name": "Cara", "email": "cara@example.com"}])
    d1 = client.get(f"/api/groups/{g1}").json()
    d2 = client.get(f"/api/groups/{g2}").json()
    ana1 = uuid.UUID(next(m["id"] for m in d1["members"] if m["name"] == "Ana"))
    ben = uuid.UUID(next(m["id"] for m in d1["members"] if m["name"] == "Ben"))
    ana2 = uuid.UUID(next(m["id"] for m in d2["members"] if m["name"] == "Ana"))
    cara = uuid.UUID(next(m["id"] for m in d2["members"] if m["name"] == "Cara"))

    rng = random.Random(11)
    for group_id, payer, other, me in [(g1, ana1, ben, ana1), (g2, ana2, cara, ana2)]:
        for _ in range(10):
            cents = rng.randint(100, 50000)
            add_expense(
                client,
                group_id,
                rng.choice([payer, other]),
                [payer, other],
                amount=f"{cents // 100}.{cents % 100:02d}",
            )

    with Session(engine) as session:
        from app.models import User
        from sqlmodel import select

        ana_id = session.exec(select(User).where(User.email == "ana@example.com")).first().id
        matching = find_my_memberships(session, ana_id)
        snaps = owed_owe_snapshots(session, matching)
        owed = owe = 0
        for group_id, my_id in matching.items():
            net = compute_counterparty_balances(session, group_id, my_id)
            for v in net.values():
                if v > 0:
                    owed += v
                else:
                    owe += -v

    assert snaps[-1][1] == owed
    assert snaps[-1][2] == owe


def test_bucket_range_forward_fills_from_last_snapshot():
    today = date.today()
    snapshots = [(today - timedelta(days=3), 500, 200)]
    bucketed = bucket_range(snapshots, "5d")
    assert len(bucketed) == 5
    days = [d for d, _, _ in bucketed]
    assert days == [today - timedelta(days=i) for i in range(4, -1, -1)]
    # Two days before the snapshot: no activity yet.
    assert bucketed[0] == (today - timedelta(days=4), 0, 0)
    # From the snapshot day onward, the snapshot's totals carry forward.
    assert bucketed[1] == (today - timedelta(days=3), 500, 200)
    assert bucketed[-1] == (today, 500, 200)


def test_bucket_range_unknown_key_raises():
    with pytest.raises(KeyError):
        bucket_range([], "bogus")
