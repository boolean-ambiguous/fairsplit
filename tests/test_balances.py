import random

from sqlmodel import Session

from app.services.balances import compute_balances


def add_expense(client, group_id, description, amount, payer_id, participants):
    return client.post(
        f"/groups/{group_id}/expenses",
        data={
            "description": description,
            "amount": amount,
            "payer_id": str(payer_id),
            "participants": [str(p) for p in participants],
        },
    )


def balances(engine, group_id):
    with Session(engine) as session:
        return compute_balances(session, group_id)


def test_payer_is_owed(client, engine, group_with_members):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    add_expense(client, group_id, "Dinner", "60.00", 1, [1, 2, 3])
    assert balances(engine, group_id) == {1: 4000, 2: -2000, 3: -2000}


def test_balances_offset_across_expenses(client, engine, group_with_members):
    group_id = group_with_members(["Ana", "Ben", "Cara"])
    add_expense(client, group_id, "Dinner", "60.00", 1, [1, 2, 3])
    add_expense(client, group_id, "Taxi", "30.00", 2, [1, 2, 3])
    assert balances(engine, group_id) == {1: 3000, 2: 0, 3: -3000}


def test_inactive_member_is_zero(client, engine, group_with_members):
    group_id = group_with_members(["Ana", "Ben", "Dave"])
    add_expense(client, group_id, "Dinner", "50.00", 1, [1, 2])
    assert balances(engine, group_id)[3] == 0


def test_balances_sum_to_zero_property(client, engine, group_with_members):
    group_id = group_with_members(["Ana", "Ben", "Cara", "Dave"])
    rng = random.Random(42)
    for i in range(20):
        payer = rng.randint(1, 4)
        participants = rng.sample([1, 2, 3, 4], rng.randint(1, 4))
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


def test_balances_shown_on_group_page(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    add_expense(client, group_id, "Lunch", "10.00", 1, [1, 2])
    page = client.get(f"/groups/{group_id}").text
    assert "is owed 5.00" in page
    assert "owes 5.00" in page


def test_settled_member_shown(client, group_with_members):
    group_id = group_with_members(["Ana"])
    page = client.get(f"/groups/{group_id}").text
    assert "settled up" in page


def test_expense_response_includes_balance_update(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    resp = add_expense(client, group_id, "Lunch", "10.00", 1, [1, 2])
    assert 'hx-swap-oob="true"' in resp.text
    assert "is owed 5.00" in resp.text
