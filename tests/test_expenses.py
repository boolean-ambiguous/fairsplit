import uuid

import pytest
from sqlmodel import Session

from app.services.balances import compute_balances
from app.services.money import MoneyError, format_cents, parse_amount


def expense_body(payer_id, participant_ids, **overrides):
    body = {
        "description": "Dinner",
        "amount": "60.00",
        "payer_id": str(payer_id),
        "participant_ids": [str(p) for p in participant_ids],
    }
    body.update(overrides)
    return body


def test_record_expense(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    ana, ben, cara = member_ids(group_id, ["Ana", "Ben", "Cara"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses", json=expense_body(ana, [ana, ben, cara])
    )
    assert resp.status_code == 200
    descriptions = [e["description"] for e in resp.json()["expenses"]]
    assert "Dinner" in descriptions


def test_non_positive_amount_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, [ana, ben], amount="0.00"),
    )
    assert resp.status_code == 422


def test_payer_outside_group_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(uuid.uuid4(), [ana, ben]),
    )
    assert resp.status_code == 422
    assert "Payer must be a member" in resp.json()["detail"]


def test_participant_outside_group_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, [ana, uuid.uuid4()]),
    )
    assert resp.status_code == 422


def test_empty_participants_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, []),
    )
    assert resp.status_code == 422


def test_remainder_goes_to_earliest_joined_participant(
    client, engine, group_with_members, member_ids
):
    group_id = group_with_members(["Ben", "Ana", "Cara"])
    ben, ana, cara = member_ids(group_id, ["Ben", "Ana", "Cara"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(cara, [ana, ben, cara], amount="100.00"),
    )
    assert resp.status_code == 200
    with Session(engine) as session:
        balances = compute_balances(session, group_id)
    assert balances[ben] == -3334
    assert balances[ana] == -3333
    assert balances[cara] == 10000 - 3333


def test_expense_in_unknown_group_404(client):
    payer = uuid.uuid4()
    resp = client.post(
        f"/api/groups/{uuid.uuid4()}/expenses",
        json=expense_body(payer, [payer]),
    )
    assert resp.status_code == 404


class TestParseAmount:
    def test_exact_cents(self):
        assert parse_amount("10.10") == 1010

    def test_integer_amount(self):
        assert parse_amount("25") == 2500

    def test_sub_cent_rejected(self):
        with pytest.raises(MoneyError):
            parse_amount("10.001")

    def test_garbage_rejected(self):
        with pytest.raises(MoneyError):
            parse_amount("abc")

    def test_negative_rejected(self):
        with pytest.raises(MoneyError):
            parse_amount("-5.00")


def test_format_cents():
    assert format_cents(1010) == "10.10"
    assert format_cents(-350) == "-3.50"
    assert format_cents(5) == "0.05"
