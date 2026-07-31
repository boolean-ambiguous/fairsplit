import uuid

import pytest
from sqlmodel import Session

from app.services.balances import compute_balances
from app.services.money import MoneyError, format_cents, parse_amount


def expense_data(payer_id, participant_ids, **overrides):
    data = {
        "description": "Dinner",
        "amount": "60.00",
        "payer_id": str(payer_id),
        "participants": [str(p) for p in participant_ids],
    }
    data.update(overrides)
    return data


def test_record_expense(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    ana, ben, cara = member_ids(group_id, ["Ana", "Ben", "Cara"])
    resp = client.post(
        f"/groups/{group_id}/expenses", data=expense_data(ana, [ana, ben, cara])
    )
    assert resp.status_code == 200
    assert "Dinner" in resp.text
    assert "60.00" in resp.text


def test_non_positive_amount_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(ana, [ana, ben], amount="0.00"),
    )
    assert resp.status_code == 422


def test_payer_outside_group_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(uuid.uuid4(), [ana, ben]),
    )
    assert resp.status_code == 422
    assert "Payer must be a member" in resp.text


def test_participant_outside_group_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(ana, [ana, uuid.uuid4()]),
    )
    assert resp.status_code == 422


def test_empty_participants_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(ana, []),
    )
    assert resp.status_code == 422


def test_remainder_goes_to_earliest_joined_participant(
    client, engine, group_with_members, member_ids
):
    # Ben joins before Ana; the remainder cent should follow join order,
    # not the (random, meaningless) UUID value of either member. Cara pays
    # so the payer/remainder effects don't get conflated.
    group_id = group_with_members(["Ben", "Ana", "Cara"])
    ben, ana, cara = member_ids(group_id, ["Ben", "Ana", "Cara"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(cara, [ana, ben, cara], amount="100.00"),
    )
    assert resp.status_code == 200
    with Session(engine) as session:
        balances = compute_balances(session, group_id)
    # 100.00 / 3 = 33.33 with 1 remainder cent -> earliest joiner (Ben)
    # owes 33.34, everyone else owes 33.33.
    assert balances[ben] == -3334
    assert balances[ana] == -3333
    assert balances[cara] == 10000 - 3333


def test_expense_in_unknown_group_404(client):
    payer = uuid.uuid4()
    resp = client.post(
        f"/groups/{uuid.uuid4()}/expenses",
        data=expense_data(payer, [payer]),
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
