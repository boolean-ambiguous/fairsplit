## Purpose

Exposing FairSplit's functionality as a JSON API consumed by a React + MUI single-page application, replacing server-rendered HTML entirely.

## ADDED Requirements

### Requirement: JSON API contract

The system SHALL expose group, member, expense, balance, and settlement data as JSON under `/api/*`, mirroring the behavior already specified by the `groups`, `expenses`, `balances`, and `settlements` capabilities. Validation failures SHALL be reported as a 422 response with a machine-readable error detail; not-found and malformed-identifier failures SHALL use the status codes already specified by `groups`.

#### Scenario: Group detail as one payload

- **WHEN** a client requests a group's detail endpoint
- **THEN** the response includes the group's members, expenses, per-member balances, and suggested settlements in a single JSON payload

#### Scenario: Validation error shape

- **WHEN** a request fails validation (e.g. a blank group name, a non-positive expense amount)
- **THEN** the response has status 422 and a JSON body describing the failure

### Requirement: Single-page application

The system SHALL serve a React application that reproduces the existing user-facing behavior (create/view groups, add members, record expenses in both split modes, view balances and settlements) entirely through client-side rendering against the JSON API, with no server-rendered HTML pages.

#### Scenario: App served at root

- **WHEN** a browser requests `/`
- **THEN** the React application loads and can reach every route the API exposes without a full page navigation

### Requirement: Theme and dark mode

The system SHALL use MUI's theming to apply a light and dark palette, switching automatically based on the operating system's color-scheme preference, with no manual toggle. Every text/background color pairing carried over from the design system SHALL retain its previously-verified WCAG AA contrast (≥4.5:1).

#### Scenario: Theme follows OS preference

- **WHEN** the operating system's preferred color scheme changes
- **THEN** the application's palette updates to match, without user interaction

#### Scenario: No manual theme override

- **WHEN** a user looks for a way to switch themes independently of the OS preference
- **THEN** no such control exists
