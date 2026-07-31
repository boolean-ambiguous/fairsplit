## MODIFIED Requirements

### Requirement: Group creation

The system SHALL allow creating a group with a non-empty name and SHALL assign it a unique, randomly-generated identifier that is not derived from creation order or any other sequential counter, so that identifiers cannot be guessed by enumeration.

#### Scenario: Create a group

- **WHEN** a user submits a group name of at least one non-whitespace character
- **THEN** a new group is created and appears in the group list

#### Scenario: Reject empty group name

- **WHEN** a user submits a blank or whitespace-only group name
- **THEN** no group is created and the request is rejected with a validation error

### Requirement: Group visibility

The system SHALL provide a list of all groups and a detail view per group showing its member roster. A group identifier that is not in the expected identifier format SHALL be rejected before any lookup is attempted; a well-formed identifier that does not match any group SHALL be rejected the same way a lookup failure would be, so malformed and merely-unknown identifiers reveal no information beyond "not accessible."

#### Scenario: View a group

- **WHEN** a user opens a group's detail page
- **THEN** the group's name and all of its members are displayed

#### Scenario: Unknown group

- **WHEN** a user requests a group identifier that is well-formed but does not exist
- **THEN** the system responds with a not-found error

#### Scenario: Malformed group identifier

- **WHEN** a user requests a group identifier that is not in the expected identifier format
- **THEN** the system rejects the request before attempting any lookup
