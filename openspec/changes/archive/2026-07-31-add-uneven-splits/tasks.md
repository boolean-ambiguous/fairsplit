# Tasks: add-uneven-splits

## Services

- [x] 1.1 `record_expense` accepts `exact_shares`; validate keys match participants, non-negative, sum equals amount (error names the difference)

## Routes

- [x] 2.1 Expense POST parses `split_mode` and per-participant `share_<id>` fields; exact-mode errors return 422

## Templates

- [x] 3.1 Split-mode selector and per-participant amount inputs in `_expenses.html`

## Tests

- [x] 4.1 `tests/test_uneven_splits.py`: exact split accepted incl. zero share, sum mismatch names difference, negative share rejected, share for non-participant rejected, balances reflect exact shares
- [x] 4.2 All pre-existing tests pass unchanged (even mode remains default)
