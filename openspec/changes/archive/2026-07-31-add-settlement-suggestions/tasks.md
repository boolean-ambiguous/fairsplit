# Tasks: add-settlement-suggestions

## Services

- [x] 1.1 `app/services/settlements.py`: `Payment` NamedTuple and `suggest_settlements(balances) -> list[Payment]` (greedy, deterministic, largest-first)

## Routes

- [x] 2.1 Add settlement plan to group-detail context

## Templates

- [x] 3.1 `_settlements.html` partial ("X pays Y amount" / "no payments needed")
- [x] 3.2 Include in `group_detail.html`; refresh with the balances out-of-band block

## Tests

- [x] 4.1 `tests/test_settlements.py`: two-party, one-creditor-many-debtors, empty plan, n−1 bound, zero-sum after applying plan (randomized), determinism, page rendering
