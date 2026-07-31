# Proposal: add-design-system

## Why

The current stylesheet grew ad hoc across four feature changes — a `:root` with a handful of colors, some inline `style="..."` attributes on form elements for one-off layout. It works, but it isn't a system: there's no documented scale, no consistent component treatment, no dark mode, and no way to check "does this still meet accessible contrast" other than eyeballing it.

## What Changes

- Formalize the existing palette into documented design tokens (color, spacing, radius, type scale) as CSS custom properties, with a full dark-mode token set activated via `prefers-color-scheme: dark`.
- Every page declares `<meta name="color-scheme" content="light dark">` so native form controls and scrollbars adapt too.
- Replace inline styles in templates with real component classes (`.btn`, `.field`, `.badge-positive/negative/muted`) with defined hover/focus-visible/disabled states.
- All text/background color pairs in both themes meet WCAG AA contrast (≥4.5:1) — verified by a computed test, not eyeballed.
- Visual behavior only — no change to routes, data, or the four existing capabilities.

## Capabilities

### New Capabilities

- `design-system`: token definitions, component styling contract, dark mode, and accessible contrast as testable requirements.

### Modified Capabilities

_None — this changes presentation only; `groups`, `expenses`, `balances`, `settlements` behavior is untouched._

## Non-goals

- A component library or build step (still plain CSS, no framework/bundler).
- User-toggleable theme switch — dark mode follows OS preference only (`prefers-color-scheme`), no persisted override.
- Redesigning information architecture or adding new UI features.

## Impact

- Rewrite `app/static/style.css` around documented tokens; no new dependencies.
- Update templates (`_expenses.html`, `_balances.html`, `_members.html`, `base.html`) to use component classes instead of inline styles.
- New tests: `tests/test_design_system.py` (contrast computation, color-scheme meta, absence of inline styles, component class presence).
