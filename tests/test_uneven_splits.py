import uuid
from datetime import date

import pytest
from sqlmodel import Session

from app.services.balances import compute_balances
from app.services.expenses import ExpenseError, validate_exact_shares

TODAY = date.today().isoformat()


def post_exact(client, group_id, amount, payer_id, shares):
    body = {
        "description": "Dinner",
        "amount": amount,
        "date": TODAY,
        "payer_id": str(payer_id),
        "split_mode": "exact",
        "participant_ids": [str(m) for m in shares],
        "exact_shares": {str(k): v for k, v in shares.items()},
    }
    return client.post(f"/api/groups/{group_id}/expenses", json=body)


def test_exact_split_accepted_with_zero_share(
    client, engine, group_with_members, member_ids
):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    ana, ben, cara = member_ids(group_id, ["Ana", "Ben", "Cara"])
    resp = post_exact(
        client,
        group_id,
        "60.00",
        ana,
        {ana: "35.00", ben: "25.00", cara: "0.00"},
    )
    assert resp.status_code == 200
    with Session(engine) as session:
        assert compute_balances(session, group_id) == {
            ana: 2500,
            ben: -2500,
            cara: 0,
        }


def test_blank_share_counts_as_zero(client, engine, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = post_exact(client, group_id, "10.00", ana, {ana: "10.00", ben: ""})
    assert resp.status_code == 200
    with Session(engine) as session:
        assert compute_balances(session, group_id) == {ana: 0, ben: 0}


def test_sum_mismatch_names_difference(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = post_exact(
        client, group_id, "60.00", ana, {ana: "35.00", ben: "24.99"}
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "59.99" in detail
    assert "0.01" in detail
    assert "missing" in detail


def test_sum_overshoot_named(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = post_exact(
        client, group_id, "60.00", ana, {ana: "35.00", ben: "25.01"}
    )
    assert resp.status_code == 422
    assert "too much" in resp.json()["detail"]


def test_negative_share_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = post_exact(
        client, group_id, "10.00", ana, {ana: "15.00", ben: "-5.00"}
    )
    assert resp.status_code == 422


def test_even_mode_remains_default(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Lunch",
            "amount": "10.00",
            "date": TODAY,
            "payer_id": str(ana),
            "participant_ids": [str(ana), str(ben)],
        },
    )
    assert resp.status_code == 200
    by_member = {
        uuid.UUID(b["member_id"]): b["balance_cents"] for b in resp.json()["balances"]
    }
    assert by_member[ana] == 500


def test_validate_exact_shares_requires_participant_match():
    with pytest.raises(ExpenseError, match="cover exactly"):
        validate_exact_shares(1000, [1, 2], {1: 1000})
    with pytest.raises(ExpenseError, match="cover exactly"):
        validate_exact_shares(1000, [1], {1: 500, 2: 500})
