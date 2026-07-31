# FairSplit

A small expense-splitting web app — groups, shared expenses, balances,
settle-up suggestions, and a personal dashboard — built **spec-first** with
[OpenSpec](https://github.com/Fission-AI/OpenSpec) to demonstrate what
spec-driven development looks like in practice, including through a full
architecture migration.

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

## The eight change cycles

Each feature followed the same loop — **propose → validate → implement → test
→ archive** — and each step is a separate commit, so the full story is
readable in `git log`:

| Change | What it added | Spec highlights |
|---|---|---|
| [`add-group-expense-tracking`](openspec/changes/archive/2026-07-31-add-group-expense-tracking/) | Groups, members, evenly split expenses | Integer-cent money; deterministic remainder allocation, shares always sum exactly to the total |
| [`add-balance-tracking`](openspec/changes/archive/2026-07-31-add-balance-tracking/) | Per-member net balances | Zero-sum invariant spec'd and tested as a property over randomized expense sets |
| [`add-settlement-suggestions`](openspec/changes/archive/2026-07-31-add-settlement-suggestions/) | "Who pays whom" plan | Greedy algorithm with a spec'd *n−1* payment bound; true minimality documented as a non-goal (it's subset-sum-hard) |
| [`add-uneven-splits`](openspec/changes/archive/2026-07-31-add-uneven-splits/) | Exact-amount splits | A **MODIFIED** delta: the even-split requirement is RENAMED and rewritten to cover both modes — the spec evolves, it isn't append-only |
| [`add-design-system`](openspec/changes/archive/2026-07-31-add-design-system/) | Design tokens, dark mode, component classes | Accessible contrast (WCAG ≥4.5:1) is a spec'd, *computed* requirement — token values were checked against the luminance formula before being written down |
| [`add-uuid-primary-keys`](openspec/changes/archive/2026-07-31-add-uuid-primary-keys/) | Unguessable group URLs | Switching to random ids broke a hidden assumption (autoincrement id order = join order) in two other places — the spec had to be corrected, not just the code |
| [`add-react-mui-frontend`](openspec/changes/archive/2026-07-31-add-react-mui-frontend/) | JSON API + React/MUI SPA, replacing Jinja2/HTMX | The largest single change in the project: a **REMOVED** capability delta (`design-system`, superseded) alongside a new one, landed atomically because a half-migrated intermediate state isn't meaningfully safer, just slower |
| [`add-dashboard`](openspec/changes/archive/2026-07-31-add-dashboard/) | Personal dashboard with a balance-trend chart | A spec'd invariant proven algebraically before it was ever run — sum of daily buckets equals the existing balance aggregate by construction, then verified as a property test |

Four moments worth clicking into:

1. **The tests caught a spec bug.** The first spec's remainder scenario
   claimed 100.00 ÷ 3 leaves *two* remainder cents (it leaves one). The
   implementation followed the spec's rule, the test suite flagged the
   arithmetic, and the spec was corrected before archiving — see the
   `feat: implement group & expense tracking` commit.
2. **Requirements change shape, not just grow.** `add-uneven-splits` renames
   and rewrites an existing requirement (`RENAMED` + `MODIFIED` deltas), and
   the merge into the live spec was verified before implementation started.
3. **A structural change forced a spec change nobody planned for.**
   `add-uuid-primary-keys` swapped autoincrement ids for random UUIDs — and in
   doing so broke a hidden coupling where "ascending member id" secretly meant
   "join order." The expense-splitting spec had to be reworded to describe
   join order explicitly instead of relying on an accident of the old id
   scheme; the settlement tie-break's *lack* of a change is recorded in
   `design.md` as a considered-and-rejected alternative, not a silent gap.
4. **A big rewrite is still spec-driven.** `add-react-mui-frontend` replaced
   the entire UI layer — Jinja2/HTMX/hand-rolled CSS for a React+MUI SPA and a
   JSON API — as one atomic OpenSpec change. Reading the four untouched
   domain specs end-to-end *before* starting confirmed they were already
   framework-agnostic (no MODIFIED delta needed); `design-system` was REMOVED
   with a Reason/Migration pointing at the new `frontend` capability, and its
   exact WCAG-verified color values were carried into the MUI theme unchanged
   — not re-derived.

## What the specs bought here

- The design decision to **materialize expense shares at write time**
  (cycle 1) made every later cycle touching balances/settlements nearly free
  — including, three cycles later, the dashboard's flow chart, which reuses
  `compute_balances` directly with zero changes to it.
- Every user-visible behavior in `openspec/specs/` has a WHEN/THEN scenario
  and a corresponding test — 82 tests, including property-style checks
  (shares sum to totals; balances sum to zero; settlement plans zero every
  balance within the *n−1* bound; the dashboard's daily balance-trend series
  sums exactly to the existing balance aggregate over randomized multi-group
  data).
- The `add-react-mui-frontend` migration is the strongest evidence the specs
  were written at the right altitude: `groups`, `expenses`, `balances`, and
  `settlements` — none of them mention HTML, Jinja2, or HTMX anywhere — needed
  *zero* changes when the entire rendering layer was replaced.

## Running it

```bash
# backend
pip install -e ".[dev]"

# frontend (separate terminal)
cd frontend && npm install && npm run build

uvicorn app.main:app --reload
# open http://127.0.0.1:8000/
```

For frontend development with hot reload, run `npm run dev` in `frontend/`
instead of `npm run build` — Vite's dev server proxies `/api` requests to the
FastAPI backend (see `frontend/vite.config.ts`), so run `uvicorn app.main:app
--reload` alongside it.

Tests and spec validation (same as CI):

```bash
pytest
openspec validate --all --strict
cd frontend && npm run lint && npm run build
```

## Stack

Python 3.11 · FastAPI (JSON API) · SQLModel/SQLite · React · TypeScript ·
MUI · Vite. Money is integer cents everywhere; domain logic lives in
`app/services/` and has no framework dependency — the same `app/services/`
code survived the frontend rewrite in `add-react-mui-frontend` untouched.

## Repo layout

```
openspec/
  specs/            # living spec: what the system does today
  changes/archive/  # one directory per completed change (the full paper trail)
app/
  services/         # domain logic (money, splits, balances, settlements, activity)
  routes/           # thin FastAPI handlers returning JSON
  schemas.py        # Pydantic response/request models
frontend/
  src/pages/        # Dashboard, GroupList, GroupDetail
  src/components/   # NicknameDialog, FlowChart
  src/api/          # typed fetch client
tests/
```
