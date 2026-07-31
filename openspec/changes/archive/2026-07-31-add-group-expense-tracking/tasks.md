# Tasks: add-group-expense-tracking

## Models

- [x] 1.1 Add `Group`, `Member`, `Expense`, `ExpenseShare` SQLModel tables in `app/models.py`

## Services

- [x] 2.1 `app/services/money.py`: `parse_amount(str) -> int` cents parser rejecting >2 decimals and non-positive amounts
- [x] 2.2 `app/services/expenses.py`: `split_evenly(amount_cents, participant_ids) -> dict[int, int]` with ascending-id remainder allocation
- [x] 2.3 `app/services/expenses.py`: `record_expense(...)` validating payer/participants membership and writing shares

## Routes

- [x] 3.1 `app/routes/groups.py`: group list + create, member add, expense create; mount router in `app/main.py`
- [x] 3.2 Validation failures return 422 with a rendered error partial

## Templates

- [x] 4.1 `group_list.html`, `group_detail.html` full pages
- [x] 4.2 `_members.html`, `_expenses.html` HTMX partials

## Tests

- [x] 5.1 `tests/conftest.py`: in-memory SQLite fixture + TestClient
- [x] 5.2 `tests/test_split.py`: even division, remainder order, single participant, property that shares sum to total
- [x] 5.3 `tests/test_groups.py`: create group, blank name rejected, duplicate member rejected, 404 on unknown group
- [x] 5.4 `tests/test_expenses.py`: record expense, non-positive amount, payer outside group, empty participants, sub-cent rejection
