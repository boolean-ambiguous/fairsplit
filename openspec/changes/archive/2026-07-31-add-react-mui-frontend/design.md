# Design: add-react-mui-frontend

## Context

MUI is a React component library, not a CSS framework — there's no way to render `<Button variant="contained">` without a React runtime, so "adopt MUI" necessarily means FastAPI stops rendering HTML and starts serving JSON, with a new SPA taking over the UI. This is the largest single change in the project so far, spanning backend, frontend, and the entire test suite, landing as one atomic cycle (see proposal.md's rationale for not splitting it).

## Decisions

### Spec-agnosticism audit, done by reading, not assuming

Read all four domain specs (`groups`, `expenses`, `balances`, `settlements`) end-to-end before starting. Result: all four describe observable behavior ("appears in the list", "rejected with a validation error", "not-found error") with no HTML-specific language — they need zero changes. `balances`/`settlements` each have one phrase written in the HTMX era ("without a full page reload" / "refresh it when a new expense is recorded") that becomes trivially, permanently true in any SPA rather than a meaningful constraint — left as-is rather than forcing a cosmetic-only delta. This is a good outcome: it validates the specs were written at the right level of abstraction from the start, exactly per OpenSpec's own guidance ("if the implementation can change without changing externally visible behavior, it likely does not belong in the spec").

### One new capability, not several

`frontend` covers the JSON API contract, SPA behavior, and theming together, rather than splitting API-vs-UI into separate capabilities. They ship atomically in this cycle, so two independently-versionable specs would be a promise not actually being kept. If something later needs to consume the JSON API without this SPA (a second client), that's the moment to split `frontend` into `api` + `web-app` via a RENAMED delta — not before.

### `design-system` REMOVED, not MODIFIED

Its four requirements (tokens, dark mode, contrast, component classes) describe a CSS-custom-property mechanism that no longer exists. Rather than force that language to describe an MUI theme, each requirement is REMOVED with a Reason/Migration pointing at `frontend`'s "Theme and dark mode" requirement, which restates the same guarantees (tokens exist, dark mode is automatic, contrast is verified) in framework-agnostic terms. The "Component classes" requirement (named CSS classes, no inline `style=`) has no equivalent in `frontend` — it doesn't map onto React/MUI's `sx`-prop styling idiom, and enforcing a specific styling convention isn't this change's job.

### MUI theme reuses the verified tokens directly — no re-derivation

The archived `add-design-system/design.md` recorded exact, WCAG-AA-verified hex values for both themes:

```
Light: bg #f7f7f5, surface #ffffff, ink #1f2328, muted #57606a,
       accent #0f766e, accent-ink #ffffff, positive #15803d,
       negative #b91c1c, border #e5e7eb
Dark:  bg #0f1115, surface #1a1d23, ink #e8e8e6, muted #9aa4b2,
       accent #5eead4, accent-ink #08201d, positive #4ade80,
       negative #fca5a5, border #2a2f3a
```

These map directly onto `createTheme({ palette: { mode, background: {default, paper}, text: {primary, secondary}, primary, success, error, divider } })` per mode in `frontend/src/theme.ts`. `mode` is driven by `useMediaQuery('(prefers-color-scheme: dark)')` — same "OS preference only" behavior as before.

One simplification MUI buys for free: hover/focus-visible/disabled states no longer need hand-written CSS (`.btn:hover { filter: brightness(1.1) }`, `:focus-visible { outline: ... }`) — MUI computes these from the base palette via `alpha()` internally. The one piece of real interactive *behavior* (not just styling) that needs a deliberate port: `_expenses.html`'s split-mode toggle (show/hide exact-amount fields via a vanilla `onchange` handler) becomes a React `useState` + conditional `TextField` render.

### API shape

`app/schemas.py` defines Pydantic response models (`GroupOut`, `MemberOut`, `ExpenseOut`, `BalanceOut`, `SettlementOut`, `GroupDetailOut`). `GroupDetailOut` bundles members/expenses/balances/settlements in one payload — actually simpler than the current OOB-swap orchestration, since the SPA can just re-fetch or merge one response instead of coordinating multiple out-of-band swaps. Expense-create request bodies keep amounts as decimal *strings* (`"amount": "60.00"`), not JS floats, so `app/services/money.parse_amount` remains the single source of truth for money parsing — reused unchanged.

### Serving model

FastAPI serves `frontend/dist/` as static files at `/` (with an `index.html` fallback for client-side routes) — single origin, no CORS needed in production. Local dev uses Vite's dev-server proxy (`/api` → `http://localhost:8000`) instead. `/` in this cycle serves the SPA shell routing to the group list; the dashboard (next change) explicitly takes over `/` from this handoff.

### Test rewrite, not test deletion

All ~55 existing test functions get rewritten to assert JSON shapes via `TestClient` against `/api/*` — the coverage doesn't shrink, only the assertion style changes (JSON structure instead of substring-matching rendered HTML). `test_design_system.py` is the one exception: its entire premise (CSS custom properties in a stylesheet that no longer exists) is gone, so it's deleted outright rather than adapted. The contrast-checking property it tested isn't ported to a new automated check in this cycle — recorded as a non-goal below, since re-verifying contrast would mean writing a same-shape check against `theme.ts` and there's no evidence yet that the ported values need re-checking (they're literally copied, not re-chosen).

### CI: build/lint/typecheck, not Playwright

New `frontend` CI job: `npm ci`, lint, `tsc --noEmit`, `vite build`. Playwright stays a manual pass after implementation — this project has never run it in CI (confirmed by reading the archived `add-design-system/design.md`, which explicitly frames the Playwright pass as the manual verification step), so this isn't scaling back existing rigor, just continuing the existing practice.

## Non-goals

- No visual redesign beyond what MUI's components naturally look like — reproduce current UX, don't redesign it.
- No re-verification of contrast as an automated test in this cycle (values are reused unchanged, not re-chosen).
- No Playwright-in-CI.
- No data migration concerns beyond Cycle A's (still no auth, still disposable local SQLite state).

## Risks / Trade-offs

- This is one large diff touching nearly every file in the repo, unlike every previous additive cycle. Accepted per proposal.md's reasoning: splitting it would mean landing a JSON-only intermediate state whose HTML-compatibility plumbing is pure throwaway the moment the SPA lands.
