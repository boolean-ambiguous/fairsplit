## Purpose

Giving FairSplit a documented, consistent visual language — tokens, components, and dark mode — instead of ad hoc CSS, with accessibility as a checked property rather than an assumption.

## ADDED Requirements

### Requirement: Design tokens

The system SHALL define its color, spacing, radius, and type-scale values as CSS custom properties in `app/static/style.css`, rather than hard-coded values scattered across rules. The token set SHALL include, at minimum: `--color-bg`, `--color-surface`, `--color-ink`, `--color-muted`, `--color-accent`, `--color-accent-ink`, `--color-positive`, `--color-negative`, `--color-border`, `--space-1` through `--space-4`, and `--radius`.

#### Scenario: Tokens present in the stylesheet

- **WHEN** the stylesheet is served
- **THEN** its `:root` block declares every token in the minimum set

### Requirement: Dark mode

The system SHALL provide a complete dark-mode token set that overrides every color token, activated automatically via an `@media (prefers-color-scheme: dark)` block. No separate light/dark markup or JavaScript SHALL be required. Every page SHALL declare `<meta name="color-scheme" content="light dark">` so native form controls and scrollbars follow the same preference.

#### Scenario: Dark token override exists

- **WHEN** the stylesheet is served
- **THEN** it contains a `prefers-color-scheme: dark` media block that redefines every color token declared in `:root`

#### Scenario: Pages declare color-scheme support

- **WHEN** any page is rendered
- **THEN** its `<head>` includes `<meta name="color-scheme" content="light dark">`

### Requirement: Accessible contrast

Every text-on-background color token pairing used by the application (ink/muted/accent/positive/negative, each against both `--color-surface` and `--color-bg`) SHALL meet a WCAG contrast ratio of at least 4.5:1, in both the light and dark token sets.

#### Scenario: All token pairs pass AA contrast

- **WHEN** the WCAG contrast ratio is computed for every (text token, background token) pair in the minimum set, in both light and dark themes
- **THEN** every ratio is at least 4.5:1

### Requirement: Component classes

Interactive elements (buttons, text/select inputs, checkboxes) and status indicators (positive/negative/settled balances) SHALL use named component classes defined in the stylesheet, with visible `:hover` and `:focus-visible` states on interactive elements. Templates SHALL NOT use inline `style` attributes for styling that a component class can express.

#### Scenario: No inline styles in rendered pages

- **WHEN** any page or HTMX partial is rendered
- **THEN** its HTML contains no `style="..."` attributes

#### Scenario: Focus state defined for interactive elements

- **WHEN** the stylesheet is served
- **THEN** it defines a `:focus-visible` rule applying to buttons, text inputs, and selects
