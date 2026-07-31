# Proposal: add-uuid-primary-keys

## Why

Every id in FairSplit is currently a sequential autoincrement integer. Group URLs (`/groups/1`, `/groups/2`, ...) are trivially enumerable — anyone can walk the id space and view every group in the app, including its members and expenses. There is no auth layer (by design, per earlier non-goals), so unguessable identifiers are the only practical barrier against casual enumeration.

## What Changes

- All four tables (`Group`, `Member`, `Expense`, `ExpenseShare`) switch their primary key from autoincrement `int` to a randomly-generated `uuid.UUID` (v4), assigned client-side at object construction.
- Group URLs and all API-facing ids become UUIDs. A malformed id in a URL is rejected (422) before any database lookup; a well-formed but unknown id still 404s normally — so guessing gets no information back either way.
- `Member` gains a `created_at` timestamp (missing until now) because member-listing order and expense-remainder allocation currently piggyback on autoincrement id order — that coupling breaks once ids are random, so creation order needs its own explicit field.
- Expense remainder-cent allocation changes from "lowest member id" to "earliest-joined participant" — the same intent (a stable, deterministic tie-break), now expressed via an explicit timestamp instead of an incidental property of autoincrement ids.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `groups`: adds an explicit requirement that group identifiers are unguessable (malformed ids rejected before lookup; unknown-but-valid ids indistinguishable from a 404 either way).
- `expenses`: the "Split modes" requirement's remainder-allocation rule changes from "ascending member-id order" to "ascending member join-order" (earliest-added participant first).

## Non-goals

- No change to `settlements`' tie-break rule. `suggest_settlements` ties are still broken by comparing member ids directly — under UUIDs this remains fully deterministic (UUIDs are totally ordered) but the specific member who wins a tie is no longer meaningfully "first joined." Considered coupling it to join order like the expense-remainder rule and rejected: `suggest_settlements` is a pure function with no DB access today, and making it order-aware would require the caller to pass a secondary sort key through for a purely cosmetic property (only visible when two members owe/are owed *exactly* equal amounts). Not worth the coupling.
- No data migration path. The existing SQLite file uses int ids; this change assumes a fresh schema (`fairsplit.db` is gitignored, disposable local state), consistent with the project's existing "no migrations" posture (`init_db()` just calls `create_all`).

## Impact

- `app/models.py`: all 4 PK fields, all 5 FK fields → `uuid.UUID`; `Member.created_at` added.
- `app/routes/groups.py`: path/form param types; `group_members`/`group_expenses` ordering switches from id to `created_at`.
- `app/services/expenses.py`: `split_evenly`'s contract changes from "sorts ids, remainder to lowest" to "remainder to the first N entries of the given (caller-ordered) list"; `record_expense` becomes responsible for resolving that order from the DB.
- `tests/conftest.py` and 5 test files: replace every hardcoded sequential-id assumption (`group_id = 1`, `payer_id: "1"`, `participants: ["1","2","3"]`) with real ids read back from the test DB.
