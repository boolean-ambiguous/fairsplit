# Proposal: add-group-expense-tracking

## Why

FairSplit currently has no domain features — just a skeleton. The foundation of any expense-splitting product is the ability to organize people into groups and record who paid for what. Nothing else (balances, settlements) can exist without this.

## What Changes

- Users can create a group with a name and add members to it by name.
- Users can record an expense in a group: description, amount, who paid, and which members participate.
- Expense amounts are split evenly among participants; remainder cents are distributed deterministically (first participants by member id absorb one extra cent each) so shares always sum to the total.
- A group page lists its members and expenses; all interactions are server-rendered forms enhanced with HTMX.
- Amounts are entered as decimal currency but stored as integer cents.

## Capabilities

### New Capabilities

- `groups`: creating groups, adding members, viewing a group's roster.
- `expenses`: recording expenses with payer and participants, even splitting with deterministic remainder allocation, listing a group's expenses.

### Modified Capabilities

_None — this is the first feature change._

## Non-goals

- Balances or settlement calculations (future changes).
- Uneven/custom splits — every expense splits evenly for now.
- Authentication, multi-tenancy, currencies other than a single implicit one.
- Editing or deleting expenses after creation.

## Impact

- New SQLModel tables: `group`, `member`, `expense`, `expenseshare`.
- New service module `app/services/expenses.py` (split logic).
- New route module `app/routes/groups.py`; templates for group list/detail.
- Tests: `tests/test_groups.py`, `tests/test_expenses.py`, `tests/test_split.py`.
