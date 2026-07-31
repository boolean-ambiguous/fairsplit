import random
import uuid

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


def test_plan_included_in_group_detail(client, group_with_members, member_ids):
    group_id = group_with_members(["Ana", "Ben"])
    ana, ben = member_ids(group_id, ["Ana", "Ben"])
    client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": "Lunch",
            "amount": "10.00",
            "payer_id": str(ana),
            "participant_ids": [str(ana), str(ben)],
        },
    )
    detail = client.get(f"/api/groups/{group_id}").json()
    settlements = [
        (uuid.UUID(s["from_member"]), uuid.UUID(s["to_member"]), s["amount_cents"])
        for s in detail["settlements"]
    ]
    assert settlements == [(ben, ana, 500)]


def test_settled_group_has_empty_plan(client, group_with_members):
    group_id = group_with_members(["Ana", "Ben"])
    detail = client.get(f"/api/groups/{group_id}").json()
    assert detail["settlements"] == []
