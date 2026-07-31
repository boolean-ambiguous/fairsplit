# balances Specification

## Purpose
Showing each group member their net position — how much the group owes them or they owe the group — derived from recorded expenses.
## Requirements
### Requirement: Net balance per member

The system SHALL compute, for every member of a group, a net balance equal to the total cents they paid as expense payer minus the total cents of their shares across all expenses. The balances of all members in a group MUST sum to exactly zero.

#### Scenario: Payer is owed money

- **WHEN** Ana pays 60.00 split evenly among Ana, Ben and Cara
- **THEN** Ana's balance is +40.00 and Ben and Cara each have -20.00

#### Scenario: Balances offset across expenses

- **WHEN** Ana pays 60.00 split among Ana, Ben, Cara and Ben pays 30.00 split among the same three
- **THEN** Ana's balance is +30.00, Ben's is 0.00 and Cara's is -30.00

#### Scenario: Member with no activity

- **WHEN** a member has paid nothing and participates in no expenses
- **THEN** that member's balance is 0.00

### Requirement: Balance visibility

The system SHALL display each member's balance on the group detail page, marking whether the member is owed money or owes money, and SHALL refresh the display when a new expense is recorded.

#### Scenario: Balances on group page

- **WHEN** a user opens a group's detail page
- **THEN** every member is listed with their formatted balance and an indication of direction (owed / owes / settled)

#### Scenario: Balances update after new expense

- **WHEN** a user records a new expense from the group page
- **THEN** the displayed balances reflect the new expense without a full page reload

