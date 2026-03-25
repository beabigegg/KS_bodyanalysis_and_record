## MODIFIED Requirements

### Requirement: Display parameter differences
The system SHALL display recipe comparison results as section-based diff views and SHALL include parameter classification fields such as stage and category for parameter rows.

#### Scenario: Show only differences
- **WHEN** compare is requested with diff-only mode enabled
- **THEN** the system SHALL return and display only rows whose values differ across the selected imports

#### Scenario: Show all parameters
- **WHEN** compare is requested with show-all mode enabled
- **THEN** the system SHALL return and display both differing and non-differing rows

#### Scenario: Filter differences by file type
- **WHEN** the user applies a file type filter such as `PRM`
- **THEN** the system SHALL limit the parameter comparison rows to matching file types

#### Scenario: Parameter exists on one machine but not another
- **WHEN** a parameter exists on one selected import but is missing on another selected import
- **THEN** the system SHALL mark that row as `is_diff = true`
- **AND** the missing side SHALL be represented as null/empty in the comparison values

#### Scenario: BSG params excluded from params section
- **WHEN** the compare response is built for the parameter section
- **THEN** the system SHALL exclude `file_type = 'BSG'` parameter rows from the parameter diff dataset
- **AND** BSG differences SHALL remain available in the dedicated BSG section

#### Scenario: Param rows include stage and category
- **WHEN** the compare API returns parameter rows
- **THEN** each parameter row SHALL include `stage` and `category` fields derived from `param_name` and `file_type`

#### Scenario: Parameters grouped by stage and category in UI
- **WHEN** the user views the parameter comparison section
- **THEN** the UI SHALL organize parameter rows by their semantic grouping data

#### Scenario: Unclassified params displayed under _unmapped
- **WHEN** a parameter row is classified with `stage = "_unmapped"`
- **THEN** the UI SHALL still include that row in the parameter comparison output

#### Scenario: Compare results are loaded one section at a time
- **WHEN** a user opens or switches compare result sections
- **THEN** the client SHALL request only the active section instead of downloading every section in one response

#### Scenario: Compare section results are paged
- **WHEN** a compare section contains more rows than the configured page size
- **THEN** the compare API SHALL return a bounded page of rows together with total row count and total pages
