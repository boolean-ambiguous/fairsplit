## RENAMED Requirements

- FROM: `### Requirement: Even split with deterministic remainder`
- TO: `### Requirement: Split modes`

## MODIFIED Requirements

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
