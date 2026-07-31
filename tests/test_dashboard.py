import random
import uuid
from datetime import date, timedelta

import pytest
from sqlmodel import Session

from app.services.activity import (
    daily_balance_series,
    filter_range,
    find_matching_members,
    group_summary_order,
)
from app.services.balances import compute_balances


def create_group(client, name):
    resp = client.post("/api/groups", json={"name": name})
    assert resp.status_code == 201
    return uuid.UUID(resp.json()["id"])


def add_member(client, group_id, name):
    resp = client.post(f"/api/groups/{group_id}/members", json={"name": name})
    assert resp.status_code == 200
    return next(
        uuid.UUID(m["id"]) for m in resp.json()["members"] if m["name"] == name
    )


def add_expense(client, group_id, payer_id, participant_ids, amount="10.00"):
    return client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Expense",
            "amount": amount,
            "payer_id": str(payer_id),
            "participant_ids": [str(p) for p in participant_ids],
        },
    )


def test_nickname_matches_per_group_independently(client, engine):
    g1 = create_group(client, "Trip A")
    g2 = create_group(client, "Trip B")
    add_member(client, g1, "Ana")
    add_member(client, g2, "Ben")

    with Session(engine) as session:
        matching = find_matching_members(session, "ana")
    assert set(matching.keys()) == {g1}


def test_nickname_case_insensitive(client, engine):
    g1 = create_group(client, "Trip")
    add_member(client, g1, "Ana")
    with Session(engine) as session:
        matching = find_matching_members(session, "ANA")
    assert g1 in matching


def test_group_ordering_active_groups_first(client, engine):
    older = create_group(client, "Older activity")
    newer = create_group(client, "Newer activity")
    a1 = add_member(client, older, "Ana")
    a2 = add_member(client, newer, "Ana")
    add_expense(client, older, a1, [a1])
    add_expense(client, newer, a2, [a2])

    with Session(engine) as session:
        ordered, _ = group_summary_order(session, [older, newer])
    assert ordered == [newer, older]


def test_group_ordering_inactive_groups_last(client, engine):
    active = create_group(client, "Active")
    inactive = create_group(client, "Inactive")
    a1 = add_member(client, active, "Ana")
    add_member(client, inactive, "Ana")
    add_expense(client, active, a1, [a1])

    with Session(engine) as session:
        ordered, _ = group_summary_order(session, [inactive, active])
    assert ordered == [active, inactive]


def test_dashboard_endpoint_returns_ordered_groups_and_balances(client):
    g1 = create_group(client, "Trip A")
    ana1 = add_member(client, g1, "Ana")
    ben1 = add_member(client, g1, "Ben")
    add_expense(client, g1, ana1, [ana1, ben1], amount="20.00")

    resp = client.get("/api/dashboard", params={"nickname": "Ana"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["groups"][0]["name"] == "Trip A"
    assert body["groups"][0]["balance_cents"] == 1000


def test_dashboard_requires_nickname(client):
    resp = client.get("/api/dashboard", params={"nickname": "   "})
    assert resp.status_code == 422


def test_dashboard_rejects_unknown_range(client):
    resp = client.get("/api/dashboard", params={"nickname": "Ana", "range": "bogus"})
    assert resp.status_code == 422


def test_flow_series_sums_to_aggregate_balance_property(client, engine):
    g1 = create_group(client, "Group 1")
    g2 = create_group(client, "Group 2")
    ids1 = [add_member(client, g1, n) for n in ["Ana", "Ben", "Cara"]]
    ids2 = [add_member(client, g2, n) for n in ["Ana", "Dave"]]

    rng = random.Random(11)
    for group_id, ids in [(g1, ids1), (g2, ids2)]:
        for i in range(15):
            payer = rng.choice(ids)
            participants = rng.sample(ids, rng.randint(1, len(ids)))
            cents = rng.randint(1, 50000)
            add_expense(
                client,
                group_id,
                payer,
                participants,
                amount=f"{cents // 100}.{cents % 100:02d}",
            )

    with Session(engine) as session:
        matching = find_matching_members(session, "Ana")
        series = daily_balance_series(session, matching)
        aggregate = sum(
            compute_balances(session, group_id)[member_id]
            for group_id, member_id in matching.items()
        )
    assert sum(series.values()) == aggregate


def test_filter_range_fills_zeros_and_covers_full_window():
    today = date.today()
    series = {today: 500}
    sliced = filter_range(series, "5d")
    assert len(sliced) == 5
    assert sliced[-1] == (today, 500)
    assert all(cents == 0 for d, cents in sliced[:-1])
    assert [d for d, _ in sliced] == [today - timedelta(days=i) for i in range(4, -1, -1)]


def test_filter_range_unknown_key_raises():
    with pytest.raises(KeyError):
        filter_range({}, "bogus")
