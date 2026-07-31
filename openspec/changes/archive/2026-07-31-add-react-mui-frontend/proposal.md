# Proposal: add-react-mui-frontend

## Why

The app currently renders HTML server-side with Jinja2/HTMX and a hand-rolled CSS design-token system. Adopting MUI — the real mui.com component library, confirmed explicitly, not a lighter "Material-style CSS" option — requires a React runtime, since MUI's components only exist as React components with no server-rendered-HTML equivalent. This means FastAPI's role shifts from rendering pages to serving a JSON API, with a new React + TypeScript SPA taking over the UI entirely.

## What Changes

- FastAPI routes move under `/api/groups...` and return JSON instead of HTML/HTMX partials. `app/services/*` (money, expenses, balances, settlements) is reused completely unchanged — only the route layer's output format changes.
- A new `frontend/` package (Vite + React + TypeScript + MUI) replaces Jinja2/HTMX/the hand-rolled CSS entirely. FastAPI serves the built app as static files at `/`.
- The MUI theme is built directly from the WCAG-verified color tokens recorded in the archived `add-design-system` change — reused, not re-derived — with `mode` driven by `prefers-color-scheme` (no manual toggle, same non-goal as before).
- All ~55 existing backend tests are rewritten to assert JSON responses instead of scraping rendered HTML.
- CI gains a `frontend` job (lint, typecheck, build). Playwright verification stays a manual pass after implementation, consistent with this project's established practice (not previously run in CI).

## Capabilities

### New Capabilities

- `frontend`: the JSON API contract, SPA routing/pages, and theme/dark-mode behavior, covered as one capability since they ship atomically in this cycle.

### Modified Capabilities

_None._ `groups`, `expenses`, `balances`, and `settlements` were audited line-by-line: their requirements describe observable behavior, not HTML — they need no changes. (`balances`/`settlements` each have one HTMX-era phrase — "without a full page reload" / "refresh it when a new expense is recorded" — that becomes trivially true in a SPA rather than a meaningful constraint; left as-is rather than forcing a cosmetic delta.)

### Removed Capabilities

- `design-system`: superseded by `frontend`. Its token values aren't lost — they're the literal source for the new MUI theme (see design.md).

## Non-goals

- No visual redesign — the SPA reproduces the current UX (group list/detail, member/expense forms, balances, settlements), not a new layout.
- No Playwright-in-CI — stays a manual verification pass, matching how every previous cycle was actually verified.

## Impact

- New: `frontend/` (Vite+React+TS+MUI), `app/schemas.py` (Pydantic response models).
- Rewritten: `app/routes/groups.py`, `app/main.py`, all 7 test files (`test_design_system.py` deleted outright), `.github/workflows/ci.yml`.
- Deleted: `app/templates/*.html`, `app/static/style.css`, `app/static/htmx.min.js`.
