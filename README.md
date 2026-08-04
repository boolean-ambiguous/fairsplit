# FairSplit

A mobile-first expense-splitting web app for small groups — roommates, trips,
anything shared. Real magic-link accounts, multi-currency groups, flexible
splits, a personal dashboard with a balance-trend chart, and a full edit
history on every expense.

## Features

- **Accounts**: sign up with email, confirm via a magic link, then pick the
  name your groups will see you by.
- **Dashboard**: a chart of what's owed to you vs. what you owe over time,
  your open positions with each person, and the groups you're in.
- **Groups**: a name, a default currency, an optional photo, and people
  invited by name (and optionally email — if they already have an account,
  they're linked immediately; otherwise they're linked automatically the
  moment they sign up with that email).
- **Expenses**: description, amount, date, an optional receipt photo, notes,
  and a two-step split — split evenly among whoever was there, or split by
  exact amount per person. Anyone in the group can edit an expense; only
  whoever paid it can delete it. Every expense has a details page with a full
  version history (who created it, who changed what, and when).
- **Settling up**: mark a balance as paid and it's recorded with a date,
  offsetting the group's balances from then on. The group detail page also
  shows a minimal-transaction settlement plan for the whole group.
- **Appearance**: a dark/light theme toggle in the account menu, persisted
  per account.

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

Tests and lint (same as CI):

```bash
pytest
cd frontend && npm run lint && npm run build
```

### Email delivery

No email provider is configured. Magic links are logged to the backend's
console (`app/services/email.py`) instead of being sent — copy the link from
there when testing signup locally. Swap that module's body for a real
provider (Postmark, SES, Resend, ...) to send actual email.

## Stack

Python 3.11 · FastAPI (JSON API, cookie sessions) · SQLModel/SQLite · React ·
TypeScript · MUI · Vite. Money is integer cents everywhere; domain logic
lives in `app/services/` and has no framework dependency.

## Repo layout

```
app/
  services/         # domain logic (money, splits, balances, settlements,
                     # activity/dashboard math, auth, email)
  routes/           # thin FastAPI handlers returning JSON
  models.py         # SQLModel tables
  schemas.py        # Pydantic request/response models
frontend/
  src/pages/        # Dashboard, GroupDetail
  src/auth/         # signup / verify / name pages + auth context
  src/components/   # dialogs (create/edit group, add/edit expense, expense
                     # details, settle up), account menu, balance chart
  src/api/          # typed fetch client
tests/
```
