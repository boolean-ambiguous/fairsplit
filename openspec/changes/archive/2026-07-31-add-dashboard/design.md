# Design: add-dashboard

## Context

Everything the dashboard needs already exists in `compute_balances` and the `Expense`/`ExpenseShare` tables — this is a read-only aggregation layer, not new domain logic, with one exception: bucketing by day is genuinely new.

## Decisions

### The flow invariant is provable, not just tested

`compute_balances` is fully decomposable per-expense: each expense contributes exactly `(amount_cents if member is payer else 0) − (share_cents if member has a share on it else 0)` to that member's group balance, and the group total is the sum of these contributions across every expense. Bucketing each expense's contribution by `DATE(Expense.created_at)` and summing across every group where the nickname matches means the sum of all daily buckets, over unbounded history, equals the sum of `compute_balances(group)[my_member_id]` across those groups — algebraically, not approximately. `tests/test_dashboard.py` asserts this as a property over randomized multi-group expense sets, the same "verify the property, don't eyeball it" pattern as the balance zero-sum and settlement *n−1*-bound tests.

The `range` parameter is implemented as a pure slice over the same unbounded series computed for the invariant test — not a second query path — so the invariant reasoning actually applies to what's served.

### UTC calendar-day bucketing, named as a simplification

`Expense.created_at` is stored in UTC. Bucketing by UTC calendar day means a user's local "today" can span two buckets near midnight in their timezone. Accepted and documented here rather than silently chosen — timezone-aware bucketing would need a stored user timezone, which doesn't exist and isn't worth adding for this.

### 1-day range: one bucket, not hourly

Daily buckets make the 1-day range nearly degenerate (0-1 data points). Special-casing hourly buckets for just that range would mean two bucketing implementations, breaking the "one function, sliced by range" property that makes the invariant reasoning clean. Accepted as a single-bar view.

### Chart: BarChart, not LineChart

Activity is spiky — discrete expense-adding events, not a continuous process. A line chart visually implies interpolation between points that don't represent anything continuous; a bar per bucket is honest about the data's actual shape. `@mui/x-charts`'s `BarChart` is MIT-licensed (no license key needed for this use) and reads its colors directly from the MUI theme already built in `add-react-mui-frontend` — no separate color configuration.

### Naming honesty

No capability in this system writes a "payment happened" row — `suggest_settlements` only ever proposes a plan (confirmed by reading `app/services/settlements.py` and the schema: there's no table for recorded payments). A chart of this data can only move in response to new expenses, never in response to someone actually paying someone back. Calling it "money flow" would misrepresent that. It's labeled "balance trend" throughout the UI and this spec, and recording real settlements is written down as a non-goal — a natural candidate for a future change, explicitly not this one.

### Nickname: client-side only, matched per group

The nickname lives in `localStorage` and is sent as a query parameter on dashboard requests — no server-side session or cookie. Matching happens independently per group (a different `Member.id` may match in each group, which is correct: `groups` already guarantees unique-per-group names, so at most one match per group is possible by construction).

## Non-goals

- Recording real-world settlement payments.
- Server-side accounts or sessions.
- Sub-day granularity for the 1-day range.

## Risks / Trade-offs

- The invariant only holds over the unbounded series; any future change that adds a second, independently-computed "windowed" code path would silently break the guarantee this design relies on. Flagged here so it isn't reintroduced by accident.
