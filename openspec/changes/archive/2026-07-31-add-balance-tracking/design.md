# Design: add-balance-tracking

## Context

Balances are a pure aggregation over data that add-group-expense-tracking already materializes (`Expense.amount_cents` per payer, `ExpenseShare.share_cents` per member). No schema change is needed.

## Decisions

### Compute on read, no stored balance

`compute_balances(session, group_id) -> dict[member_id, int]` runs two grouped sums (paid by payer, owed by share) and subtracts. At showcase scale this is O(rows in group); caching or denormalized balance columns would only add invalidation risk.

### Zero-sum invariant as a test property

Because shares always sum exactly to their expense amount (guaranteed by `split_evenly`), balances per group must sum to zero. The test suite asserts this property over randomized expense sets — it would catch any future split-logic regression from the balance side too.

### HTMX out-of-band swap for updates

The expense-create partial response includes the balances block marked `hx-swap-oob="true"`, so one POST updates both the expense list (normal target) and the balances card without extra requests.

## Risks / Trade-offs

- Recomputing on every page view is wasteful at large scale — accepted; correctness and simplicity win for this project's scope.
