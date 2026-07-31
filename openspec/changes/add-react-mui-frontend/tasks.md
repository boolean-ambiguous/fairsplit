# Tasks: add-react-mui-frontend

## Backend

- [ ] 1.1 `app/schemas.py`: `GroupOut`, `MemberOut`, `ExpenseOut`, `BalanceOut`, `SettlementOut`, `GroupDetailOut`
- [ ] 1.2 `app/routes/groups.py` rewritten under `/api/groups`: JSON in/out, reuse `app/services/*` unchanged, structured 422 error bodies
- [ ] 1.3 `app/main.py`: drop Jinja2Templates; serve `frontend/dist/` at `/` with SPA fallback
- [ ] 1.4 `pyproject.toml`: drop `jinja2`; drop `python-multipart` if no form-encoded endpoints remain
- [ ] 1.5 Delete `app/templates/*.html`, `app/static/style.css`, `app/static/htmx.min.js`

## Frontend

- [ ] 2.1 Scaffold `frontend/` (Vite + React + TS), install `@mui/material`, `@emotion/react`, `@emotion/styled`, `react-router-dom`
- [ ] 2.2 `frontend/src/theme.ts`: MUI theme from ported tokens, `mode` via `prefers-color-scheme`
- [ ] 2.3 `frontend/src/api/client.ts`: typed fetch wrapper
- [ ] 2.4 `frontend/src/pages/GroupList.tsx`, `GroupDetail.tsx`; `App.tsx` routing
- [ ] 2.5 Split-mode toggle as `useState` + conditional `TextField`s
- [ ] 2.6 Vite dev-server proxy config for local dev against uvicorn

## Tests

- [ ] 3.1 Rewrite all 6 surviving test files to assert JSON via `TestClient` against `/api/*`
- [ ] 3.2 Delete `tests/test_design_system.py`

## CI

- [ ] 4.1 Add `frontend` job to `.github/workflows/ci.yml` (Node 22, npm ci, lint, typecheck, build)

## Verification

- [ ] 5.1 `pytest` green against JSON
- [ ] 5.2 `openspec validate --all --strict` (new `frontend` capability, `design-system` removed)
- [ ] 5.3 `frontend` CI job green
- [ ] 5.4 Manual Playwright pass: create group → add members → add expense (both split modes) → balances/settlements shown, in light and dark
- [ ] 5.5 Confirm no manual theme toggle exists
