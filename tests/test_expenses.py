import pytest

from app.services.money import MoneyError, format_cents, parse_amount


def expense_data(**overrides):
    data = {
        "description": "Dinner",
        "amount": "60.00",
        "payer_id": "1",
        "participants": ["1", "2", "3"],
    }
    data.update(overrides)
    return data


def test_record_expense(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    resp = client.post(f"/groups/{group_id}/expenses", data=expense_data())
    assert resp.status_code == 200
    assert "Dinner" in resp.text
    assert "60.00" in resp.text


def test_non_positive_amount_rejected(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses", data=expense_data(amount="0.00")
    )
    assert resp.status_code == 422


def test_payer_outside_group_rejected(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses", data=expense_data(payer_id="99")
    )
    assert resp.status_code == 422
    assert "Payer must be a member" in resp.text


def test_participant_outside_group_rejected(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses",
        data=expense_data(participants=["1", "99"]),
    )
    assert resp.status_code == 422


def test_empty_participants_rejected(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    resp = client.post(
        f"/groups/{group_id}/expenses", data=expense_data(participants=[])
    )
    assert resp.status_code == 422


def test_expense_in_unknown_group_404(client):
    assert (
        client.post("/groups/999/expenses", data=expense_data()).status_code == 404
    )


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
