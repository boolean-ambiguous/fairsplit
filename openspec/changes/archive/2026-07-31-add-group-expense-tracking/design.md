# Design: add-group-expense-tracking

## Context

First feature change on a bare FastAPI skeleton. Decisions made here (data model, money handling, route/template structure) set the pattern every later change follows.

## Goals / Non-Goals

**Goals:** durable data model for groups/expenses, exact money arithmetic, server-rendered UI with HTMX partial updates.

**Non-goals:** balances, settlements, uneven splits, auth.

## Decisions

### Money as integer cents

All amounts are `int` cents end-to-end. Form input is parsed with `decimal.Decimal` and rejected if it has more than two decimal places — never `float`, which cannot represent 0.10 exactly.

### Shares materialized at write time

Each expense writes one `ExpenseShare` row per participant at creation time, rather than recomputing splits on read. Balances (next change) then become a simple aggregation over shares, and historical expenses are immune to later changes in split logic.

**Alternative considered:** compute shares on the fly from `amount / participants`. Rejected: remainder allocation would have to be re-derived identically at every read site, and future uneven splits would require a schema migration anyway.

### Deterministic remainder allocation

`split_evenly(amount_cents, participant_ids)` sorts ids ascending and gives the first `amount % n` participants one extra cent. Deterministic, order-independent, and trivially testable.

### Route/template structure

- `app/routes/groups.py` — all group/expense routes, mounted under `/groups`.
- Full pages render `group_list.html` / `group_detail.html`; HTMX form posts return partial templates (`_members.html`, `_expenses.html`) that swap into the page.
- Validation errors return HTTP 422 with the error message rendered in the partial.

## Risks / Trade-offs

- SQLite with a single implicit currency is fine for the showcase scale; the cents convention keeps a future currency field additive.
- No expense editing means mistakes require re-entry — acceptable, spec'd as a non-goal.
