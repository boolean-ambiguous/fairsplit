# Proposal: add-dashboard

## Why

The group-detail page answers "where does this group stand?" but nothing answers "where do *I* stand, across everything?" — a user in several groups has to open each one and add it up by hand. There's also no login system and none is planned, so "my groups/balance" has no server-side identity to hang off of today.

## What Changes

- `/` becomes a dashboard (taking over from the group list, which moves to `/groups`): groups ordered by most recent expense activity, a per-group balance for "me," and a chart of my balance trend over a selectable range (1 day / 5 days / 1 month / 12 months).
- "Me" is a browser-local nickname captured once (MUI dialog, persisted to `localStorage`), matched case-insensitively against `Member.name` *within each group* — no accounts, no server sessions, consistent with the app's standing no-auth stance.
- The chart plots the net daily change in my aggregate balance, derived entirely from existing expense data — not literal cash movement, since the app has no way to record a real repayment (`suggest_settlements` only ever suggests a plan; nothing persists a "paid" event). Labeled "balance trend," not "money flow," to avoid implying otherwise.

## Capabilities

### New Capabilities

- `dashboard`: group summary ordering, per-nickname balance overview, and the balance-trend series with its range parameter.

### Modified Capabilities

_None._ The dashboard is read-only over existing data — it reuses `compute_balances` directly and adds one new bucketed-aggregation function. `groups`, `expenses`, `balances`, `settlements`, and `frontend` need no changes.

## Non-goals

- Recording real-world settlement payments (marking a suggested payment as "done"). The chart's honesty depends on this being explicitly out of scope — see design.md.
- Server-side accounts/sessions — the nickname is a client-side convenience, not an identity system.
- Sub-day granularity for the 1-day range — accepted as a single bucket (see design.md).

## Impact

- New: `app/services/activity.py`, `GET /api/dashboard` route, `frontend/src/pages/Dashboard.tsx`, `NicknameDialog.tsx`, `FlowChart.tsx` (`@mui/x-charts`).
- `App.tsx` routing: `/` → Dashboard, `/groups` → GroupList (moved).
- `tests/test_dashboard.py`, including a property test that daily-bucketed flow sums to the same total as `compute_balances`.
