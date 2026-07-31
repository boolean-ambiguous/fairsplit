# FairSplit

A small expense-splitting web app — groups, shared expenses, balances, and
settle-up suggestions — built **spec-first** with
[OpenSpec](https://github.com/Fission-AI/OpenSpec) to demonstrate what
spec-driven development looks like in practice.

The app is deliberately modest. **The artifact this repo showcases is the
process**: every feature entered the codebase as a validated spec change, was
implemented against that spec, and was then archived into a living
specification of the whole system.

## Why spec-driven?

Working with AI coding agents (or human teammates) fails in predictable ways:
requirements live in chat scrollback, "done" is undefined, and six weeks later
nobody knows why the code behaves the way it does. Spec-driven development
fixes the incentive structure:

- **Intent is written before code.** A proposal says *why*, a spec delta says
  *what* (as testable WHEN/THEN scenarios), a design doc says *how* and — just
  as importantly — what was considered and rejected.
- **"Done" is checkable.** Scenarios map to tests; `openspec validate --strict`
  gates the format; CI runs both.
- **History stays legible.** Each archived change is a self-contained record:
  proposal → spec delta → design → tasks, merged into `openspec/specs/` — the
  always-current description of what the system does today.

## The five change cycles

Each feature followed the same loop — **propose → validate → implement → test
→ archive** — and each step is a separate commit, so the full story is
readable in `git log`:

| Change | What it added | Spec highlights |
|---|---|---|
| [`add-group-expense-tracking`](openspec/changes/archive/2026-07-31-add-group-expense-tracking/) | Groups, members, evenly split expenses | Integer-cent money; deterministic remainder allocation, shares always sum exactly to the total |
| [`add-balance-tracking`](openspec/changes/archive/2026-07-31-add-balance-tracking/) | Per-member net balances | Zero-sum invariant spec'd and tested as a property over randomized expense sets |
| [`add-settlement-suggestions`](openspec/changes/archive/2026-07-31-add-settlement-suggestions/) | "Who pays whom" plan | Greedy algorithm with a spec'd *n−1* payment bound; true minimality documented as a non-goal (it's subset-sum-hard) |
| [`add-uneven-splits`](openspec/changes/archive/2026-07-31-add-uneven-splits/) | Exact-amount splits | A **MODIFIED** delta: the even-split requirement is RENAMED and rewritten to cover both modes — the spec evolves, it isn't append-only |
| [`add-design-system`](openspec/changes/archive/2026-07-31-add-design-system/) | Design tokens, dark mode, component classes | Accessible contrast (WCAG ≥4.5:1) is a spec'd, *computed* requirement — token values were checked against the luminance formula before being written down, and a test re-checks every pairing on every run |

Two moments worth clicking into:

1. **The tests caught a spec bug.** The first spec's remainder scenario
   claimed 100.00 ÷ 3 leaves *two* remainder cents (it leaves one). The
   implementation followed the spec's rule, the test suite flagged the
   arithmetic, and the spec was corrected before archiving — see the
   `feat: implement group & expense tracking` commit. Specs are code-reviewable
   claims, not decoration.
2. **Requirements change shape, not just grow.** `add-uneven-splits` doesn't
   bolt on a new capability; it renames and rewrites an existing requirement
   (`RENAMED` + `MODIFIED` delta operations), and the merge into the live spec
   was verified before implementation started.

## What the specs bought here

- The design decision to **materialize expense shares at write time**
  (cycle 1) made cycles 2–4 nearly free: balances are a pure aggregation,
  settlements a pure function, and uneven splits touched one write path while
  balances/settlements needed zero changes. That reasoning is written down in
  each `design.md`, including the alternatives that were rejected.
- Every user-visible behavior in `openspec/specs/` has a WHEN/THEN scenario
  and a corresponding test — 78 tests, including property-style checks
  (shares sum to totals; balances sum to zero; settlement plans zero every
  balance within the *n−1* bound; every design-system color pairing clears
  WCAG AA contrast in both light and dark themes).

## Running it

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/groups
```

Tests and spec validation (same as CI):

```bash
pytest
openspec validate --all --strict
```

## Stack

Python 3.11 · FastAPI · SQLModel/SQLite · Jinja2 · HTMX (vendored, no build
step). Money is integer cents everywhere; domain logic lives in
`app/services/` and is framework-free.

## Repo layout

```
openspec/
  specs/            # living spec: what the system does today
  changes/archive/  # one directory per completed change (the full paper trail)
app/
  services/         # domain logic (money, splits, balances, settlements)
  routes/           # thin FastAPI handlers
  templates/        # Jinja2 + HTMX partials
tests/
```
