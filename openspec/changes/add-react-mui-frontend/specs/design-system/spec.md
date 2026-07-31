## REMOVED Requirements

### Requirement: Design tokens

**Reason**: Superseded by the `frontend` capability's "Theme and dark mode" requirement. The CSS custom-property token set this required no longer exists — the same color values now live in an MUI theme object instead of `app/static/style.css`.

**Migration**: The exact token values (`--color-bg` through `--color-border`, and the WCAG-verified light/dark pairs) are carried forward unchanged into `frontend/src/theme.ts`'s MUI palette, as recorded in this change's `design.md`. No values were re-derived.

### Requirement: Dark mode

**Reason**: Superseded by `frontend`'s "Theme and dark mode" requirement, which restates the same behavior (automatic `prefers-color-scheme` switching, no manual toggle) in framework-agnostic terms rather than CSS-media-query terms.

**Migration**: See `frontend` capability. The `<meta name="color-scheme">` tag requirement is preserved as part of the new SPA's `index.html`.

### Requirement: Accessible contrast

**Reason**: Superseded by `frontend`'s "Theme and dark mode" requirement, which restates the same ≥4.5:1 AA contrast guarantee without reference to CSS custom properties.

**Migration**: The verified hex values are unchanged; contrast was already checked once and does not need re-deriving. The computed contrast test (`tests/test_design_system.py`) is not carried forward as an automated backend test in this change — see design.md's non-goals for the rationale.

### Requirement: Component classes

**Reason**: This requirement was specific to hand-written CSS class names and an "no inline `style=` attributes" rule for Jinja2-rendered HTML. Neither concept maps onto React/MUI, where styling idiomatically happens via the `sx` prop and theme-aware component variants rather than named CSS classes, and there is no server-rendered HTML to inspect for inline styles.

**Migration**: MUI's built-in component states (hover, focus-visible, disabled) replace the hand-written CSS states this requirement described — see design.md. No equivalent requirement is added; enforcing a specific React styling convention is out of scope for this change.
