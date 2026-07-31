# Proposal: add-settlement-suggestions

## Why

Balances tell members where they stand but not what to do about it. The natural next question — "who should pay whom?" — currently requires mental arithmetic. A settlement plan turns balances into a short list of concrete payments.

## What Changes

- The group page shows a "Settle up" section: a list of payments (from-member, to-member, amount) that would bring every balance to zero.
- The plan uses a greedy largest-debtor-pays-largest-creditor algorithm, guaranteeing at most `members − 1` payments.
- The plan is a suggestion only — recording an actual repayment stays out of scope.
- The section refreshes together with balances when a new expense is recorded.

## Capabilities

### New Capabilities

- `settlements`: computing a minimal-length payment plan that zeroes all group balances.

### Modified Capabilities

_None — balances and expenses are unchanged; settlements is a pure function of balances._

## Non-goals

- Truly minimal *number* of transactions in the NP-hard sense (subset-sum matching); greedy's `n − 1` bound is the guarantee we spec.
- Recording repayments or marking debts as paid.
- Notifications or payment-provider integration.

## Impact

- New service `app/services/settlements.py`.
- Group detail context and `_balances.html`/new `_settlements.html` partial.
- Tests: `tests/test_settlements.py`.
