# Design: add-settlement-suggestions

## Context

Settlements consume `compute_balances` output — a zero-sum dict of member → cents. The interesting decision is the algorithm and its guarantees.

## Decisions

### Greedy max-debtor → max-creditor

Repeatedly match the largest debtor with the largest creditor and transfer `min(debt, credit)`; the fully-satisfied side drops out. Each step retires at least one member, so a group of `n` members needs at most `n − 1` payments.

**Alternative considered:** exact minimal transaction count. That is subset-sum-hard (finding zero-sum subgroups), gains at most a payment or two for realistic group sizes, and would make the spec's guarantee harder to state. The spec deliberately promises the `n − 1` bound, not optimality.

### Determinism as a spec'd requirement

Heaps with (amount, member_id) tie-breaks make output stable across runs. Determinism matters because the plan is user-visible; a plan that reshuffles on refresh looks broken even when correct.

### Pure function, no storage

`suggest_settlements(balances) -> list[Payment]` takes the balances dict, touches no database, and returns a `NamedTuple` list. Trivial to test exhaustively.

## Risks / Trade-offs

- Greedy can miss a smaller plan (e.g. two disjoint pairs that exactly cancel). Accepted and documented in the proposal's non-goals.
