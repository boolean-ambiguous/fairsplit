# Tasks: add-uuid-primary-keys

## Models

- [x] 1.1 `app/models.py`: all 4 PKs → non-Optional `uuid.UUID` with `default_factory=uuid.uuid4`; all 5 FK fields → `uuid.UUID`; add `Member.created_at`

## Services

- [x] 2.1 `app/services/expenses.py`: `split_evenly` contract change (remainder to first N of given list, no internal sort); `record_expense` resolves participant order from DB (`Member.created_at`) before calling it
- [x] 2.2 `app/services/balances.py`, `app/services/settlements.py`: type hint updates only (`dict[uuid.UUID, int]`)

## Routes

- [x] 3.1 `app/routes/groups.py`: path/form param types → `uuid.UUID`; `group_members()`/`group_expenses()` ordering → `created_at`

## Tests

- [x] 4.1 `tests/conftest.py`: `group_with_members` reads real ids back from the DB instead of hardcoding `group_id = 1`
- [x] 4.2 `tests/test_expenses.py`, `test_design_system.py`, `test_uneven_splits.py`, `test_settlements.py`, `test_balances.py`: replace hardcoded `"1"`/`"2"`/`"3"` member-id literals with real ids
- [x] 4.3 `tests/test_split.py`: replace `test_remainder_is_order_independent` with a test of the new order-dependent contract
- [x] 4.4 `tests/test_groups.py`: `test_unknown_group_404` uses a syntactically-valid nonexistent UUID; add a malformed-UUID-422 test
- [x] 4.5 New test: first-added member (not lowest-UUID member) receives the remainder cent

## Verification

- [x] 5.1 `pytest` green; grep test payloads for stray sequential-id literals as a smell check
- [x] 5.2 Manual: `/groups/<random-uuid>` 404s, `/groups/not-a-uuid` 422s
