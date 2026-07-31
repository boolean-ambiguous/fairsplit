## Purpose

Organizing people into named groups so shared expenses can be tracked against a fixed roster of members.

## ADDED Requirements

### Requirement: Group creation

The system SHALL allow creating a group with a non-empty name and SHALL assign it a unique identifier.

#### Scenario: Create a group

- **WHEN** a user submits a group name of at least one non-whitespace character
- **THEN** a new group is created and appears in the group list

#### Scenario: Reject empty group name

- **WHEN** a user submits a blank or whitespace-only group name
- **THEN** no group is created and the request is rejected with a validation error

### Requirement: Group membership

The system SHALL allow adding members to a group by name. Member names MUST be unique within their group (case-insensitive).

#### Scenario: Add a member

- **WHEN** a user adds the name "Ana" to a group with no member of that name
- **THEN** "Ana" appears in the group's member roster

#### Scenario: Reject duplicate member name

- **WHEN** a user adds a name that already exists in the group, ignoring case
- **THEN** no member is created and the request is rejected with a validation error

### Requirement: Group visibility

The system SHALL provide a list of all groups and a detail view per group showing its member roster.

#### Scenario: View a group

- **WHEN** a user opens a group's detail page
- **THEN** the group's name and all of its members are displayed

#### Scenario: Unknown group

- **WHEN** a user requests a group identifier that does not exist
- **THEN** the system responds with a not-found error
