## MODIFIED Requirements

### Requirement: Summary-first import detail browsing
The system SHALL present import detail as a summary-first browsing flow instead of forcing users to load all parameter rows before they can orient themselves. The parameter table SHALL only display classification columns that are meaningful for the current file type.

#### Scenario: Import detail opens with section overview
- **WHEN** a user opens an import detail page
- **THEN** the system SHALL show top-level counts for parameter data and specialized sections before loading parameter row tables

#### Scenario: Parameter data is browsed incrementally
- **WHEN** a user filters by file type, parameter group, stage, category, process step, or keyword
- **THEN** the system SHALL narrow the displayed parameter dataset without forcing the user to scan the entire recipe payload at once

#### Scenario: PRM parameters display all classification columns including process_step
- **WHEN** a user views PRM file type parameters
- **THEN** the table SHALL display process_step, param_group, stage, category, family, feature, instance, tunable, and description columns

#### Scenario: Non-PRM non-REF non-PHY parameters hide all classification columns
- **WHEN** a user views parameters of file type AIC, BND, HB, LF, LHM, MAG, PPC, VHM, or WIR
- **THEN** the table SHALL NOT display process_step, param_group, stage, category, family, feature, instance, tunable, or description columns

#### Scenario: PHY and REF parameters hide classification columns except param_group
- **WHEN** a user views parameters of file type PHY or REF
- **THEN** the table SHALL display param_group but SHALL NOT display process_step, stage, category, family, feature, instance, tunable, or description columns

#### Scenario: Compare mode hides unused classification columns
- **WHEN** a user compares parameters across imports
- **THEN** the comparison table SHALL hide classification columns that are empty for all displayed rows

### Requirement: Guided parameter facets
The system SHALL expose guided parameter facets derived from stored parameter semantics so users can narrow large imports without relying on raw text search alone.

#### Scenario: File type and semantic facet options are available
- **WHEN** a user enters the parameter browsing view for an import
- **THEN** the system SHALL provide available file types, parameter groups, stages, categories, process steps, and richer PRM semantics such as family and feature for that import

#### Scenario: Parameter facet options reflect current filter context
- **WHEN** the user applies one or more parameter filters
- **THEN** the available facet options and counts SHALL update to reflect the remaining matching dataset

#### Scenario: PRM browser can group documented unmapped families
- **WHEN** the user browses PRM parameters such as `SF*` or `SL*`
- **THEN** the browser SHALL let the user organize those rows by semantic family and feature instead of leaving them in an undifferentiated unmapped bucket

#### Scenario: Process step facet filters by manufacturing flow order
- **WHEN** the user selects a process step facet value (e.g. "0. 燒球 (EFO / Ball Formation)")
- **THEN** the system SHALL filter to show only parameters belonging to that manufacturing process step

#### Scenario: Process step facet options are ordered by step number
- **WHEN** the process step facet is displayed
- **THEN** the options SHALL be ordered by the numeric prefix (0, 2, 3, 4, 5, 6, 7) reflecting the actual wire bonding process flow

### Requirement: Export parameters
The system SHALL let users export the currently filtered parameter dataset as CSV.

#### Scenario: Export filtered parameters includes process_step
- **WHEN** the user exports parameter rows from the detail page
- **THEN** the exported CSV SHALL contain the currently filtered parameter dataset including the `process_step` column for PRM parameters
