# expenses Specification

## Purpose
Recording who paid for what within a group, and splitting each expense's cost across its participants so every cent is accounted for.
## Requirements
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

### Requirement: Split modes

The system SHALL support two ways of splitting an expense among its participants, chosen per expense, with shares always stored in integer cents that sum exactly to the expense amount.

**Even mode (default):** the system SHALL split the amount evenly among participants. When the amount is not evenly divisible, the remainder cents SHALL be assigned one each to participants in ascending member-id order.

**Exact mode:** the user provides each participant's share in cents. The system SHALL reject the expense unless the provided shares sum exactly to the expense amount. Individual shares MAY be zero, but every share MUST be non-negative.

#### Scenario: Even division

- **WHEN** 60.00 is split evenly among 3 participants
- **THEN** each participant's share is 20.00

#### Scenario: Remainder distribution

- **WHEN** 100.00 is split evenly among 3 participants
- **THEN** the participant with the lowest member id owes 33.34 and the other two owe 33.33 each, summing to 100.00

#### Scenario: Single participant

- **WHEN** an expense has exactly one participant
- **THEN** that participant's share equals the full amount

#### Scenario: Exact split accepted

- **WHEN** a user records 60.00 in exact mode with shares 35.00, 25.00 and 0.00
- **THEN** the expense is created with exactly those shares

#### Scenario: Exact shares must sum to the amount

- **WHEN** a user records 60.00 in exact mode with shares totalling 59.99 or 60.01
- **THEN** no expense is created and the error names the difference between the shares total and the amount

#### Scenario: Negative share rejected

- **WHEN** a user records an expense in exact mode with any negative share
- **THEN** no expense is created and the request is rejected with a validation error

