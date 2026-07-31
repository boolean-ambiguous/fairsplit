# Proposal: add-uneven-splits

## Why

Real group expenses are rarely perfectly even — one person had the steak, another only a starter. Forcing every expense into an even split makes balances subtly wrong, which undermines the whole point of tracking them.

## What Changes

- Expense entry gains a split mode: **even** (existing behavior, default) or **exact amounts**.
- In exact mode the user enters each participant's share; shares MUST sum exactly to the expense amount or the expense is rejected.
- A participant share of zero is allowed in exact mode (present at dinner, consumed nothing) — but at least one share must be positive.
- Even mode, balances and settlements are untouched; shares remain materialized rows, so downstream capabilities need no changes.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `expenses`: the "Even split with deterministic remainder" requirement becomes "Split modes" — even split keeps its exact behavior and remains the default, and an exact-amounts mode is added with a sum-must-match constraint.

## Non-goals

- Percentage or shares/weights-based splitting.
- Editing the split of an existing expense.
- Changing how balances or settlements consume shares (they already read materialized rows).

## Impact

- `app/services/expenses.py`: `record_expense` accepts optional exact shares; new validation.
- Expense form gains a mode toggle and per-participant amount inputs (HTMX).
- `tests/test_uneven_splits.py`; existing split tests continue to pass unchanged.
