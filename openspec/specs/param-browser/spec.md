## Requirements

### Requirement: Browse recipe import records
The system SHALL let users browse imported recipe records with machine and product filters.

#### Scenario: View import list with filters
- **WHEN** the user opens the import browsing page
- **THEN** the UI SHALL list recipe imports with fields such as machine type, machine id, product type, BOP, wafer PN, recipe time, and import time

#### Scenario: Filter by machine and product
- **WHEN** the user applies machine or product filters
- **THEN** the system SHALL narrow the import list to matching imports

#### Scenario: Search by keyword
- **WHEN** the user searches by keyword
- **THEN** the system SHALL match import records by fields such as `product_type`, `bop`, `wafer_pn`, and `recipe_name`

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

### Requirement: Compare parameter selection reuses classification-first browsing
The system SHALL present compare parameter selection with the same file-type-first and classification-aware browsing model used in Recipe Import Records parameter view.

#### Scenario: Compare selection starts from file type overview
- **WHEN** the user enters the parameter selection step for compare
- **THEN** the UI SHALL present available file types for the selected imports before asking the user to choose parameter rows

#### Scenario: Compare selection offers guided facets for the chosen file type
- **WHEN** the user narrows the compare parameter catalog
- **THEN** the system SHALL offer only the classification facets that are meaningful for the active file type, including `param_group` and `process_step` for `PRM`

#### Scenario: Compare selection can browse union parameter catalog
- **WHEN** a parameter exists on some selected imports but not others
- **THEN** the compare parameter selection view SHALL still list that parameter as a selectable item

### Requirement: Compare selection uses file-type-aware classification columns
The system SHALL apply the same file-type-specific classification column visibility rules in compare parameter selection as in import detail parameter browsing.

#### Scenario: PRM compare selection displays PRM classification columns
- **WHEN** the user views `PRM` parameters in compare selection
- **THEN** the selection table SHALL display `process_step`, `param_group`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, and `description`

#### Scenario: PHY and REF compare selection hide unsupported classification columns
- **WHEN** the user views `PHY` or `REF` parameters in compare selection
- **THEN** the selection table SHALL display `param_group`
- **AND** the selection table SHALL NOT display `process_step`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, or `description`

#### Scenario: Other file types hide all classification columns
- **WHEN** the user views parameters of file type `AIC`, `BND`, `HB`, `LF`, `LHM`, `MAG`, `PPC`, `VHM`, or `WIR` in compare selection
- **THEN** the selection table SHALL NOT display `process_step`, `param_group`, `stage`, `category`, `family`, `feature`, `instance`, `tunable`, or `description`
