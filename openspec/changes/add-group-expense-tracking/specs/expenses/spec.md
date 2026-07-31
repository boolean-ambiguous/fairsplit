## Purpose

Recording who paid for what within a group, and splitting each expense's cost across its participants so every cent is accounted for.

## ADDED Requirements

### Requirement: Expense recording

The system SHALL allow recording an expense in a group with a non-empty description, a positive amount, a payer who is a member of the group, and one or more participants who are members of the group.

#### Scenario: Record a valid expense

- **WHEN** a user records "Dinner", 60.00, paid by Ana, split among Ana, Ben and Cara
- **THEN** the expense appears in the group's expense list with its description, amount and payer

#### Scenario: Reject non-positive amount

- **WHEN** a user records an expense with amount zero or negative
- **THEN** no expense is created and the request is rejected with a validation error

#### Scenario: Reject payer outside the group

- **WHEN** a user records an expense whose payer is not a member of the group
- **THEN** no expense is created and the request is rejected with a validation error

#### Scenario: Reject empty participant list

- **WHEN** a user records an expense with no participants selected
- **THEN** no expense is created and the request is rejected with a validation error

### Requirement: Monetary precision

The system SHALL store all monetary amounts as integer cents. Amounts entered as decimal currency MUST be converted exactly, and amounts with more than two decimal places MUST be rejected.

#### Scenario: Exact cent storage

- **WHEN** a user enters an amount of 10.10
- **THEN** the stored amount is exactly 1010 cents

#### Scenario: Reject sub-cent input

- **WHEN** a user enters an amount of 10.001
- **THEN** the request is rejected with a validation error

### Requirement: Even split with deterministic remainder

The system SHALL split each expense evenly among its participants in integer cents. When the amount is not evenly divisible, the remainder cents SHALL be assigned one each to participants in ascending member-id order, so that the shares always sum exactly to the expense amount.

#### Scenario: Even division

- **WHEN** 60.00 is split among 3 participants
- **THEN** each participant's share is 20.00

#### Scenario: Remainder distribution

- **WHEN** 100.00 is split among 3 participants
- **THEN** the two participants with the lowest member ids owe 33.34 and the third owes 33.33, summing to 100.00

#### Scenario: Single participant

- **WHEN** an expense has exactly one participant
- **THEN** that participant's share equals the full amount
