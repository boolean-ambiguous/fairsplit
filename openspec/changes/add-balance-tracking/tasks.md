# Tasks: add-balance-tracking

## Services

- [ ] 1.1 `app/services/balances.py`: `compute_balances(session, group_id) -> dict[int, int]` (paid minus owed per member)

## Routes

- [ ] 2.1 Include balances in group-detail context
- [ ] 2.2 Expense-create response carries an out-of-band balances swap

## Templates

- [ ] 3.1 `_balances.html` partial with owed/owes/settled styling
- [ ] 3.2 Wire partial into `group_detail.html` and `_expenses.html` (hx-swap-oob)

## Tests

- [ ] 4.1 `tests/test_balances.py`: payer-owed scenario, offsetting expenses, inactive member, zero-sum property, balances visible on page, balances present in expense-create response
