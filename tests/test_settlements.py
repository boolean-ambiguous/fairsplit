import random

from app.services.settlements import Payment, suggest_settlements


def test_two_party_debt():
    assert suggest_settlements({1: 2000, 2: -2000}) == [Payment(2, 1, 2000)]


def test_one_creditor_many_debtors():
    plan = suggest_settlements({1: 3000, 2: -1000, 3: -2000})
    assert plan == [Payment(3, 1, 2000), Payment(2, 1, 1000)]


def test_all_settled_empty_plan():
    assert suggest_settlements({1: 0, 2: 0, 3: 0}) == []


def test_no_zero_payments():
    plan = suggest_settlements({1: 500, 2: -500, 3: 0})
    assert all(p.amount_cents > 0 for p in plan)


def test_plan_is_deterministic():
    balances = {1: 700, 2: -300, 3: -400, 4: 0}
    assert suggest_settlements(balances) == suggest_settlements(dict(balances))


def test_ties_break_on_member_id():
    plan = suggest_settlements({1: 1000, 2: -500, 3: -500})
    assert plan == [Payment(2, 1, 500), Payment(3, 1, 500)]


def test_largest_payment_first():
    plan = suggest_settlements({1: 6000, 2: 5000, 3: -10000, 4: -1000})
    amounts = [p.amount_cents for p in plan]
    assert amounts == sorted(amounts, reverse=True)


def _random_balances(rng, n):
    values = [rng.randint(-50000, 50000) for _ in range(n - 1)]
    values.append(-sum(values))
    return {i + 1: v for i, v in enumerate(values)}


def test_plan_zeroes_balances_and_respects_bound():
    rng = random.Random(7)
    for _ in range(200):
        balances = _random_balances(rng, rng.randint(2, 8))
        plan = suggest_settlements(balances)
        assert len(plan) <= len(balances) - 1
        applied = dict(balances)
        for p in plan:
            applied[p.from_member] += p.amount_cents
            applied[p.to_member] -= p.amount_cents
        assert all(v == 0 for v in applied.values())


def test_plan_shown_on_group_page(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    client.post(
        f"/groups/{group_id}/expenses",
        data={
            "description": "Lunch",
            "amount": "10.00",
            "payer_id": str(ana),
            "participants": [str(ana), str(ben)],
        },
    )
    page = client.get(f"/groups/{group_id}").text
    assert "pays" in page
    assert "5.00" in page


def test_settled_group_message(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    page = client.get(f"/groups/{group_id}").text
    assert "No payments needed" in page
