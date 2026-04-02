## ADDED Requirements

### Requirement: Select recipes for comparison
The system SHALL let users choose multiple imported recipes with matching product context for comparison.

#### Scenario: Select comparison targets
- **WHEN** the user filters by identifiers such as `product_type`, `bop`, or `wafer_pn`
- **THEN** the UI SHALL present matching recipe imports grouped by machine and import context

#### Scenario: Quick compare latest recipes
- **WHEN** the user requests a quick compare for the latest available recipes
- **THEN** the system SHALL select the latest matching imports for comparison

### Requirement: Display parameter differences
The system SHALL display recipe comparison results as section-based diff views and SHALL include semantic grouping fields such as stage and category for parameter rows.

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
- **AND** the missing side SHALL be represented as null or empty in the comparison values

#### Scenario: BSG params excluded from params section
- **WHEN** the compare response is built for the parameter section
- **THEN** the system SHALL exclude `file_type = "BSG"` parameter rows from the parameter diff dataset
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

### Requirement: Include RPM data in comparison
The system SHALL include RPM limits and RPM reference datasets in comparison output.

#### Scenario: RPM sections present in compare response
- **WHEN** compare data is requested
- **THEN** the compare API SHALL expose `rpm_limits` and `rpm_reference` sections

### Requirement: Compare APP and BSG wide tables
The system SHALL compare APP and BSG datasets alongside parameter data.

#### Scenario: Compare capillary and wire specs
- **WHEN** APP data is available for the selected imports
- **THEN** the system SHALL display those APP fields in compare output

#### Scenario: Compare ball signature settings
- **WHEN** BSG data is available for the selected imports
- **THEN** the system SHALL display grouped BSG comparison output

### Requirement: Parameter selection step before compare
The system SHALL require users to choose the parameter scope after selecting imports and before loading compare results.

#### Scenario: Compare flow pauses at parameter selection
- **WHEN** the user selects two or more imports and starts a cross-machine compare
- **THEN** the UI SHALL open a parameter selection step for those imports instead of immediately requesting compare results

#### Scenario: Import changes invalidate stale parameter selection
- **WHEN** the selected import set changes after parameters have been chosen
- **THEN** the system SHALL clear the previous parameter selection
- **AND** the user SHALL be required to choose parameters again before compare can run

### Requirement: Parameter diff results honor selected scope
The system SHALL limit parameter diff output to the user-selected parameter keys while continuing to compare the chosen imports.

#### Scenario: Compare selected parameter keys
- **WHEN** the user submits compare with a set of selected `(file_type, param_name)` keys
- **THEN** the `params` compare section SHALL include only rows whose keys are in that selection
- **AND** a selected parameter that is missing on one or more imports SHALL still be returned as a diff row

#### Scenario: Non-parameter sections remain available
- **WHEN** a compare session is created from selected imports and selected parameters
- **THEN** the UI SHALL continue to provide APP, BSG, RPM Limits, and RPM Reference sections for the same import set
