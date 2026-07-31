## Purpose

Turning a group's balances into a concrete, short list of who-pays-whom payments that settles everyone.

## ADDED Requirements

### Requirement: Settlement plan

The system SHALL compute a list of payments (debtor, creditor, amount in cents) such that applying all payments brings every member's balance to exactly zero. The plan MUST contain at most one fewer payment than the group has members, and MUST contain no zero-amount payments.

#### Scenario: Simple two-party debt

- **WHEN** Ana's balance is +20.00 and Ben's is -20.00
- **THEN** the plan is exactly one payment: Ben pays Ana 20.00

#### Scenario: One creditor, several debtors

- **WHEN** Ana is +30.00, Ben is -10.00 and Cara is -20.00
- **THEN** the plan is two payments: Cara pays Ana 20.00 and Ben pays Ana 10.00

#### Scenario: All settled

- **WHEN** every member's balance is zero
- **THEN** the plan is empty

### Requirement: Deterministic plan order

The system SHALL produce the same plan for the same balances on every computation: ties between equal balances are broken by ascending member id, and the plan is ordered largest payment first.

#### Scenario: Stable output

- **WHEN** the same set of balances is computed twice
- **THEN** both plans list identical payments in identical order

### Requirement: Settlement visibility

The system SHALL display the settlement plan on the group detail page and refresh it when a new expense is recorded.

#### Scenario: Plan on group page

- **WHEN** a user opens a group page where members owe each other money
- **THEN** each suggested payment is shown as "X pays Y amount"

#### Scenario: Settled group message

- **WHEN** every member is settled
- **THEN** the section states that no payments are needed
