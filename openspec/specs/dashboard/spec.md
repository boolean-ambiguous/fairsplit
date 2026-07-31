# dashboard Specification

## Purpose
Answering "where do I stand?" across every group at a glance, using a browser-local nickname in place of an account system this app deliberately doesn't have.
## Requirements
### Requirement: Nickname identity

The system SHALL identify "me" for dashboard purposes using a client-supplied nickname, matched case-insensitively against `Member.name` independently within each group (the same matching convention `groups` already uses for duplicate-name checks). The system SHALL NOT use server-side accounts, sessions, or cookies to establish this identity.

#### Scenario: Nickname matches per group independently

- **WHEN** a nickname matches a member in one group but no member in another
- **THEN** the dashboard includes a balance for the matching group and omits one for the group with no match

#### Scenario: Case-insensitive match

- **WHEN** the nickname differs from a group's member name only in letter case
- **THEN** the two are treated as the same person

### Requirement: Group summary ordering

The system SHALL list groups ordered by their most recent expense's timestamp, descending. Groups with no expenses SHALL sort after every group that has at least one, and SHALL be ordered among themselves by group creation time, descending.

#### Scenario: Most recently active group first

- **WHEN** group A's newest expense is older than group B's newest expense
- **THEN** group B appears before group A in the dashboard's group list

#### Scenario: Inactive groups sort last

- **WHEN** a group has no expenses
- **THEN** it appears after every group that has at least one expense, regardless of when the group itself was created

### Requirement: Balance trend series

The system SHALL provide, for a nickname, a series of daily net-balance-change values bucketed by UTC calendar day, computed by attributing each expense's contribution to the nickname's matching member across every group where a match exists, summed per day. The system SHALL support filtering this series to the caller's choice of the trailing 1 day, 5 days, 1 month, or 12 months. The sum of the full, unfiltered series SHALL equal the sum of the nickname's balance across all matching groups as computed by the `balances` capability.

The system SHALL label this series in a way that does not imply real-world cash movement (e.g. "balance trend"), since no capability in this system records an actual settlement payment — only suggests one.

#### Scenario: Full series sums to current aggregate balance

- **WHEN** the unfiltered daily series is summed over a nickname's full expense history
- **THEN** the result equals the sum of that nickname's balance across every group where they have a matching member

#### Scenario: Range filters without recomputing

- **WHEN** a caller requests the 5-day range
- **THEN** the response is the trailing 5 days of the same underlying daily series, not a separately computed value

