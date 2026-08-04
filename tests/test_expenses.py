import uuid
from datetime import date, timedelta

import pytest
from sqlmodel import Session

from app.services.balances import compute_balances
from app.services.money import MoneyError, format_cents, parse_amount

TODAY = date.today().isoformat()


def expense_body(payer_id, participant_ids, **overrides):
    body = {
        "description": "Dinner",
        "amount": "60.00",
        "date": TODAY,
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
    expense = next(e for e in resp.json()["expenses"] if e["description"] == "Dinner")
    assert expense["split_mode"] == "even"
    assert expense["can_delete"] is True  # Ana (the signed-in member) is the payer


def test_non_positive_amount_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, [ana, ben], amount="0.00"),
    )
    assert resp.status_code == 422


def test_oversized_amount_rejected_cleanly(client, group_with_members, member_ids):
    # A very long digit string used to trip an uncaught decimal.InvalidOperation
    # in parse_amount() (context precision overflow on .quantize()), surfacing
    # as an unhandled 500. It must now be rejected as a clean validation error.
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, [ana, ben], amount="9" * 50),
    )
    assert resp.status_code == 422


def test_future_date_rejected(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        f"/api/groups/{group_id}/expenses",
        json=expense_body(ana, [ana, ben], date=tomorrow),
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


def test_expense_in_unknown_group_404(client, signed_in):
    signed_in("Ana")
    payer = uuid.uuid4()
    resp = client.post(
        f"/api/groups/{uuid.uuid4()}/expenses",
        json=expense_body(payer, [payer]),
    )
    assert resp.status_code == 404


def test_only_payer_can_delete(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses", json=expense_body(ben, [ana, ben])
    )
    expense_id = resp.json()["expenses"][0]["id"]
    # Ana (signed in) did not pay, so she can't delete it.
    resp = client.delete(f"/api/groups/{group_id}/expenses/{expense_id}")
    assert resp.status_code == 403


def test_anyone_can_edit_and_history_is_recorded(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses", json=expense_body(ben, [ana, ben])
    )
    expense_id = resp.json()["expenses"][0]["id"]

    resp = client.patch(
        f"/api/groups/{group_id}/expenses/{expense_id}",
        json=expense_body(ben, [ana, ben], description="Dinner (updated)", amount="80.00"),
    )
    assert resp.status_code == 200
    expense = next(e for e in resp.json()["expenses"] if e["id"] == expense_id)
    assert expense["description"] == "Dinner (updated)"
    assert expense["amount_cents"] == 8000
    assert len(expense["history"]) == 1
    fields_changed = {c["field"] for c in expense["history"][0]["changes"]}
    assert fields_changed == {"Description", "Amount"}


def test_edit_without_changes_adds_no_history(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = client.post(
        f"/api/groups/{group_id}/expenses", json=expense_body(ana, [ana, ben])
    )
    expense_id = resp.json()["expenses"][0]["id"]
    resp = client.patch(
        f"/api/groups/{group_id}/expenses/{expense_id}", json=expense_body(ana, [ana, ben])
    )
    expense = next(e for e in resp.json()["expenses"] if e["id"] == expense_id)
    assert expense["history"] == []


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
