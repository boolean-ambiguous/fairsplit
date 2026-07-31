import random
import uuid

from sqlmodel import Session

from app.services.balances import compute_balances


def add_expense(client, group_id, description, amount, payer_id, participants):
    return client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": description,
            "amount": amount,
            "payer_id": str(payer_id),
            "participant_ids": [str(p) for p in participants],
        },
    )


def balances(engine, group_id):
    with Session(engine) as session:
        return compute_balances(session, group_id)


def test_payer_is_owed(client, engine, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    ana, ben, cara = member_ids(group_id, ["Ana", "Ben", "Cara"])
    add_expense(client, group_id, "Dinner", "60.00", ana, [ana, ben, cara])
    assert balances(engine, group_id) == {ana: 4000, ben: -2000, cara: -2000}


def test_balances_offset_across_expenses(
    client, engine, group_with_members, member_ids
):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    ana, ben, cara = member_ids(group_id, ["Ana", "Ben", "Cara"])
    add_expense(client, group_id, "Dinner", "60.00", ana, [ana, ben, cara])
    add_expense(client, group_id, "Taxi", "30.00", ben, [ana, ben, cara])
    assert balances(engine, group_id) == {ana: 3000, ben: 0, cara: -3000}


def test_inactive_member_is_zero(client, engine, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben", "Dave"])
    ana, ben, dave = member_ids(group_id, ["Ana", "Ben", "Dave"])
    add_expense(client, group_id, "Dinner", "50.00", ana, [ana, ben])
    assert balances(engine, group_id)[dave] == 0


def test_balances_sum_to_zero_property(client, engine, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben", "Cara", "Dave"])
    ids = member_ids(group_id, ["Ana", "Ben", "Cara", "Dave"])
    rng = random.Random(42)
    for i in range(20):
        payer = rng.choice(ids)
        participants = rng.sample(ids, rng.randint(1, 4))
        cents = rng.randint(1, 99999)
        add_expense(
            client,
            group_id,
            f"Expense {i}",
            f"{cents // 100}.{cents % 100:02d}",
            payer,
            participants,
        )
    assert sum(balances(engine, group_id).values()) == 0


def test_balances_shown_in_group_detail(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    add_expense(client, group_id, "Lunch", "10.00", ana, [ana, ben])
    detail = client.get(f"/api/groups/{group_id}").json()
    by_member = {
        uuid.UUID(b["member_id"]): b["balance_cents"] for b in detail["balances"]
    }
    assert by_member[ana] == 500
    assert by_member[ben] == -500


def test_settled_member_has_zero_balance(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana"])
    (ana,) = member_ids(group_id, ["Ana"])
    detail = client.get(f"/api/groups/{group_id}").json()
    by_member = {
        uuid.UUID(b["member_id"]): b["balance_cents"] for b in detail["balances"]
    }
    assert by_member[ana] == 0


def test_expense_response_includes_updated_balances(
    client, group_with_members, member_ids
):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    resp = add_expense(client, group_id, "Lunch", "10.00", ana, [ana, ben])
    by_member = {
        uuid.UUID(b["member_id"]): b["balance_cents"] for b in resp.json()["balances"]
    }
    assert by_member[ana] == 500
