# Design: add-uneven-splits

## Context

This is the project's first MODIFIED-requirement change: it rewrites the expenses spec's split requirement rather than adding a capability. The materialized-shares decision from add-group-expense-tracking pays off here — balances and settlements are consumers of share rows and need zero changes.

## Decisions

### Exact shares as an optional argument, not a second code path

`record_expense(..., exact_shares: dict[int, int] | None = None)`. When `None`, `split_evenly` runs as before; when given, shares are validated (keys == participants, non-negative, sum == amount) and written as-is. One write path, one `ExpenseShare` schema, no mode column — the mode is fully determined by how shares were computed, which no reader cares about.

### Sum mismatch reported with the difference

"Shares total 59.99 but the expense is 60.00 (0.01 missing)" is spec'd behavior: off-by-a-cent is the overwhelmingly common failure mode when typing exact amounts, and naming the difference makes it fixable at a glance.

### Form UX: checkbox row grows an amount input

The participant checkboxes stay; choosing "exact amounts" reveals an amount input next to each checked participant (plain HTMX/HTML, no custom JS). Unchecked participants send no share field.

## Risks / Trade-offs

- Zero-share participants are recorded as participants with a 0-cent row. Harmless for balances (adds nothing) and keeps "who was there" queryable later.
