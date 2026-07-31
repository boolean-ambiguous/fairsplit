# Proposal: add-balance-tracking

## Why

Recording expenses is only half the product — members need to see where they stand. A group currently shows what was spent but not who owes whom, which is the question users actually open the app to answer.

## What Changes

- Each group page shows a balance per member: total paid minus total share owed, in cents.
- Positive balance means the group owes the member money; negative means the member owes the group.
- Balances are computed from materialized expense shares, so they always sum to exactly zero per group.
- Balance display updates via HTMX whenever a new expense is recorded.

## Capabilities

### New Capabilities

- `balances`: computing and displaying per-member net balances for a group.

### Modified Capabilities

_None — expense recording behavior is unchanged; balances are a pure read over existing data._

## Non-goals

- Settlement suggestions (who should pay whom to zero out) — that is the next change.
- Recording repayments/settle-up transactions.
- Cross-group or historical balance views.

## Impact

- New service `app/services/balances.py` (aggregation over `ExpenseShare`/`Expense`).
- Group detail route includes balances; new `_balances.html` partial.
- Tests: `tests/test_balances.py`.
