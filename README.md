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

Install the backend once regardless of which path below you use:

```bash
pip install -e ".[dev]"
```

### 1. Local development (hot reload)

Two servers, two terminals — the frontend proxies API calls to the backend
(see `frontend/vite.config.ts`), so both need to be running:

```bash
# terminal 1
uvicorn app.main:app --reload
# terminal 2
cd frontend && npm install && npm run dev
```

Browse **`http://localhost:5173`**. Edits to either side hot-reload. Magic
links log pointing at `:5173` automatically — no configuration needed.

### 2. Local production-style run (single server)

Build the frontend once, then run only the backend — `app/main.py` mounts
and serves `frontend/dist` itself, so there's no separate frontend process:

```bash
cd frontend && npm install && npm run build && cd ..
uvicorn app.main:app --reload
```

Browse whatever origin uvicorn is bound to (**`http://127.0.0.1:8000`** by
default). Magic links automatically point at that same origin — the backend
detects it's serving the built SPA and uses the incoming request's own
host/port, so this also works unmodified if you bind to a different port or
a loopback/private-network (LAN) IP. This auto-detection only trusts
loopback addresses, private-network IPs (RFC1918, link-local), and the
literal hostname `localhost`, since the request's `Host` header can't
otherwise be verified — if you access the app via a LAN hostname instead
(e.g. an mDNS/Bonjour name like `mylaptop.local`), set
`FAIRSPLIT_FRONTEND_URL` explicitly (see path 3 below).

### 3. Real deployment

Set `FAIRSPLIT_FRONTEND_URL` to the app's public URL:

```bash
FAIRSPLIT_FRONTEND_URL=https://fairsplit.example.com uvicorn app.main:app
```

This always takes priority over the auto-detection in path 2, which matters
behind a reverse proxy or load balancer that doesn't forward the original
`Host`/scheme faithfully, or if the frontend and backend ever end up served
from different origins.

### 4. Hosting on a custom domain (Render)

FairSplit runs as a single process — `uvicorn` serving the API and the built
SPA together — so it fits a single Render web service, no Docker required:

- Build command: `cd frontend && npm install && npm run build && cd .. && pip install -e .`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
  (`--proxy-headers` matters: Render terminates TLS at its edge and forwards
  `X-Forwarded-Proto`/`X-Forwarded-For`; without it uvicorn sees plain `http`,
  which breaks the `secure` cookie flag in `app/routes/auth.py` and reports
  every request as coming from Render's internal proxy IP, which breaks the
  per-IP signup rate limit above.)
- Render's free web-service plan has no persistent disk — its filesystem is
  wiped on every deploy/restart, which local SQLite can't survive. Use a free
  hosted Postgres instead: create a [Supabase](https://supabase.com) project,
  then copy the **Session pooler** connection string (Project Settings →
  Database → Connection string, or the "Connect" button — look for "Session
  pooler", not "Direct connection" or "Transaction pooler"). Supabase's direct
  connection hostname is IPv6-only, and Render's network has no outbound IPv6
  route, so it fails with "Network is unreachable"; the session pooler
  (Supavisor) is IPv4-reachable and behaves like a direct connection — unlike
  the transaction pooler, which multiplexes connections per-transaction and
  can break SQLAlchemy usage patterns like prepared statements — which suits
  this app's single long-running process. The pooler connection string's
  username is `postgres.<project-ref>` rather than plain `postgres`. Set the
  whole string as `FAIRSPLIT_DB` as-is (works whether it starts with
  `postgres://` or `postgresql://` — `app/database.py` routes it through the
  `psycopg` driver automatically). Supabase requires TLS; the driver
  negotiates it automatically, no extra config needed. (If you'd rather keep
  local SQLite and pay for a Render disk instead, mount one at `/var/data`
  and set `FAIRSPLIT_DB=sqlite:////var/data/fairsplit.db`.)
- Set `FAIRSPLIT_FRONTEND_URL=https://your-domain.com` (see path 3 above).
- Add the custom domain in the Render dashboard, then add the `CNAME`
  (or `ANAME`/`ALIAS` for an apex domain) it gives you at your DNS provider.
  Render auto-provisions the TLS certificate once DNS resolves.

### Tests and lint

Same commands CI runs:

```bash
pytest
cd frontend && npm run lint && npm run build
```

### Email delivery

Magic links are sent over SMTP (`app/services/email.py`, using Python's
`smtplib` — no extra dependency). By default it points at a local
[Mailpit](https://mailpit.axllent.org/) instance (`localhost:1025`, no auth),
so you can see signup emails without a real mail server:

```bash
docker run -d --name mailpit -p 8025:8025 -p 1025:1025 axllent/mailpit
# or: brew install mailpit && mailpit
```

Then sign up as usual and check `http://localhost:8025` for the email.

For production, point at a real provider's SMTP relay (e.g.
[Resend](https://resend.com), after verifying your sending domain) via env
vars — none of these have defaults that reach outside localhost, so nothing
is sent anywhere unexpected in dev:

```bash
SMTP_HOST=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=<your Resend API key>
SMTP_USE_TLS=true
EMAIL_FROM="FairSplit <noreply@your-domain.com>"
```

`/api/auth/signup` is also rate-limited (3 requests per email, 10 per IP,
per 15 minutes — see `app/services/auth.py` and `app/services/rate_limit.py`)
since it now triggers real outbound email.

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
