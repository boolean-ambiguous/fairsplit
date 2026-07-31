# Tasks: add-dashboard

## Backend

- [x] 1.1 `app/services/activity.py`: `daily_balance_series(session, nickname) -> dict[date, int]` (unbounded, UTC calendar-day buckets); `filter_range(series, range) -> list[(date, int)]` pure slice
- [x] 1.2 `app/routes/dashboard.py`: `GET /api/dashboard?nickname=...&range=1d|5d|1mo|12mo` — groups ordered by most-recent-expense (nulls-last by group creation time), per-group balance for the nickname's match, the sliced series
- [x] 1.3 `app/schemas.py`: `DashboardGroupOut`, `FlowPointOut`, `DashboardOut`
- [x] 1.4 Wire `dashboard_router` into `app/main.py`

## Frontend

- [x] 2.1 `frontend/src/pages/Dashboard.tsx` at `/`; move `GroupList` to `/groups`
- [x] 2.2 `frontend/src/components/NicknameDialog.tsx`: MUI `Dialog`, first-visit capture, `localStorage`, editable via app-bar affordance
- [x] 2.3 Install `@mui/x-charts`; `frontend/src/components/FlowChart.tsx`: `BarChart` + `ToggleButtonGroup` for the 4 ranges
- [x] 2.4 `api/client.ts` + `api/types.ts`: dashboard endpoint

## Tests

- [x] 3.1 `tests/test_dashboard.py`: invariant property test (sum of daily series == sum of compute_balances across matching groups), group-ordering tie-break (zero-expense groups, equal timestamps), nickname case-insensitivity + per-group scoping, range slicing

## Verification

- [x] 4.1 `pytest` green; `openspec validate --all --strict` (new `dashboard` capability)
- [x] 4.2 `frontend` CI job green (build includes the new page/chart)
- [x] 4.3 Manual Playwright pass: nickname dialog on first visit only, persists across reload, dashboard reflects it immediately, group ordering by activity, range toggle changes the chart, light and dark
